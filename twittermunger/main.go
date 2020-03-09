package main

import (
	"archive/tar"
	"bufio"
	"bytes"
	"compress/bzip2"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/pkg/errors"
)

// User is a user
type User struct {
	ID         int64  `json:"id"`
	ScreenName string `json:"screen_name"`
	Location   string `json:"location"`
}

// Geo is a geographical thing
type Geo struct {
	Type        string    `json:"type"`
	Coordinates []float64 `json:"coordinates"`
}

// Place is a place
type Place struct {
	ID          string `json:"id"`
	Type        string `json:"place_type"`
	Name        string `json:"name"`
	FullName    string `json:"full_name"`
	CountryCode string `json:"country_code"`
	Country     string `json:"country"`
}

// ExtendedTweet has longer text
type ExtendedTweet struct {
	FullText string `json:"full_text"`
}

// Tweet is a tweet with a User and maybe a Geo or a Place
type Tweet struct {
	ID            int64          `json:"id"`
	CreatedAt     string         `json:"created_at"`
	Text          string         `json:"text`
	User          User           `json:"user"`
	Geo           *Geo           `json:"geo"`
	Place         *Place         `json:"place"`
	ExtendedTweet *ExtendedTweet `json:"extended_tweet"`
}

// MungeOpts holds options related to tweet munging
type MungeOpts struct {
	CountryCode      string
	SearchExpr       *regexp.Regexp
	UserLocationExpr *regexp.Regexp
}

func processLine(line string, opts MungeOpts) (*Tweet, error) {
	var t Tweet
	d := json.NewDecoder(strings.NewReader(line))
	if err := d.Decode(&t); err != nil {
		return nil, errors.Wrapf(err, "process line %q", line)
	}

	if !opts.SearchExpr.MatchString(t.Text) {
		return nil, errors.New("no text match")
	}

	if !opts.UserLocationExpr.MatchString(t.User.Location) {
		return nil, errors.New("no user location match")
	}

	if opts.CountryCode == "" {
		return &t, nil
	}

	// additional filtering on place
	if t.Place == nil {
		return nil, errors.New("no place")
	}

	if t.Place.CountryCode != opts.CountryCode {
		return nil, errors.New("no country code match")
	}

	return &t, nil
}

func toCSV(w *csv.Writer, t *Tweet) {
	var countryCode, placeName, tweetText string
	if t.Place != nil {
		countryCode = t.Place.CountryCode
		placeName = t.Place.Name
	}

	if t.ExtendedTweet != nil {
		tweetText = t.ExtendedTweet.FullText
	} else {
		tweetText = t.Text
	}
	fields := []string{
		fmt.Sprintf("%d", t.ID),
		fmt.Sprintf("%d", mustParseDateToTimestamp(t.CreatedAt)),
		t.User.ScreenName,
		t.User.Location,
		placeName,
		countryCode,
		tweetText,
	}
	w.Write(fields)
	w.Flush()
}

func mustParseDateToTimestamp(s string) int64 {
	timeFmt := "Mon Jan 02 15:04:05 -0700 2006"
	t, err := time.Parse(timeFmt, s)
	if err != nil {
		panic(err)
	}
	return t.Unix()
}

func slurpTarFile(fileName string, ch chan string) error {
	tarFile, err := os.Open(fileName)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	defer tarFile.Close()

	var b bytes.Buffer
	tr := tar.NewReader(tarFile)
	for {
		b.Reset()
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		} else if err != nil {
			return err
		}

		if !strings.HasSuffix(hdr.Name, ".json.bz2") {
			continue
		}

		_, err = io.Copy(&b, tr)
		if err != nil {
			return err
		}

		bzipReader := bzip2.NewReader(&b)
		s := bufio.NewScanner(bzipReader)

		for s.Scan() {
			line := s.Text()
			if len(line) == 0 {
				continue
			}
			ch <- line
		}
	}
	return nil
}

func main() {
	var countryCode string
	var searchExpr string
	var userLocationExpr string
	var numWorkers int
	flag.StringVar(&countryCode, "country", "", "country code")
	flag.StringVar(&userLocationExpr, "userlocationexpr", ".*", "user location expression")
	flag.StringVar(&searchExpr, "searchexpr", ".*", "search expression")
	flag.IntVar(&numWorkers, "numworkers", 1, "max number of concurrent workers")
	flag.Parse()
	opts := MungeOpts{
		CountryCode:      strings.ToUpper(countryCode),
		SearchExpr:       regexp.MustCompile(searchExpr),
		UserLocationExpr: regexp.MustCompile(userLocationExpr),
	}

	writer := csv.NewWriter(os.Stdout)

	writer.Write([]string{
		"tweet_id",
		"tweet_created_at_ts",
		"user_screen_name",
		"user_location",
		"tweet_place_name",
		"tweet_place_country_code",
		"tweet_text",
	})
	args := flag.Args()
	if len(args) == 0 {
		flag.Usage()
		return
	}

	readCh := make(chan string)
	writeCh := make(chan *Tweet)
	var readWg sync.WaitGroup
	var writeWg sync.WaitGroup

	// set up some workers to do actual processing
	for i := 0; i < numWorkers; i++ {
		readWg.Add(1)
		go func() {
			for line := range readCh {
				t, err := processLine(line, opts)
				if err != nil {
					continue
				}
				if t.ID == 0 {
					continue
				}
				writeCh <- t
			}
			readWg.Done()
		}()
	}

	// set up a single worker to write to stdout
	writeWg.Add(1)
	go func() {
		for t := range writeCh {
			toCSV(writer, t)
		}
		writeWg.Done()
	}()

	// slurp up that delicious tar file
	for _, arg := range args {
		if err := slurpTarFile(arg, readCh); err != nil {
			os.Stderr.WriteString(err.Error())
			os.Exit(1)
		}
	}

	// once we're done slurping, close our read channel and wait
	// for the goroutines to finish
	close(readCh)
	readWg.Wait()

	// then close the write channel and wait for the writer to finish
	close(writeCh)
	writeWg.Wait()
}

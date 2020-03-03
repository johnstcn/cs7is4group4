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
	"time"

	"github.com/pkg/errors"
)

// User is a user
type User struct {
	ID int64 `json:"id"`
	ScreenName string `json:"screen_name"`
	Location string `json:"location"`
}

// Geo is a geographical thing
type Geo struct {
	Type string `json:"type"`
	Coordinates []float64 `json:"coordinates"`
}

// Place is a place
type Place struct {
	ID string `json:"id"`
	Type string `json:"place_type"`
	Name string `json:"name"`
	FullName string `json:"full_name"`
	CountryCode string `json:"country_code"`
	Country string `json:"country"`
}

// ExtendedTweet has longer text
type ExtendedTweet struct {
	FullText string `json:"full_text"`
}

// Tweet is a tweet with a User and maybe a Geo or a Place
type Tweet struct {
	ID int64 `json:"id"`
	CreatedAt string `json:"created_at"`
	Text string `json:"text`
	User User `json:"user"`
	Geo *Geo `json:"geo"`
	Place *Place `json:"place"`
	ExtendedTweet *ExtendedTweet `json:"extended_tweet"`
}

// TweetMunger munges tweets
type TweetMunger struct {
	CountryCode string
	SearchExpr *regexp.Regexp
	UserLocationExpr *regexp.Regexp
	Writer *csv.Writer
}

func (tm *TweetMunger) processFile(fname string) {
	f, err := os.Open(fname)
	if err != nil {
		fmt.Fprintln(os.Stderr, "ERR: open %s: %s", fname, err)
		return
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		t, err := tm.processLine(scanner.Text())
		if err != nil {
			continue
		}
		tm.toCSV(t)
	}
}

func (tm *TweetMunger) processLine(line string) (*Tweet, error) {
	var t Tweet
	d := json.NewDecoder(strings.NewReader(line))
	if err := d.Decode(&t); err != nil {
		return nil, errors.Wrapf(err, "process line %q", line)
	}

	if !tm.SearchExpr.MatchString(t.Text) {
		return nil, errors.New("no text match")
	}

	if !tm.UserLocationExpr.MatchString(t.User.Location) {
		return nil, errors.New("no user location match")
	}

	if tm.CountryCode == "" {
		return &t, nil
	}

	// additional filtering on place
	if t.Place == nil {
		return nil, errors.New("no place")
	}

	if t.Place.CountryCode != tm.CountryCode {
		return nil, errors.New("no country code match")
	}

	return &t, nil
}

func (tm *TweetMunger) toCSV(t *Tweet) {
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
	tm.Writer.Write(fields)
	tm.Writer.Flush()
}

func mustParseDateToTimestamp(s string) int64 {
	timeFmt := "Mon Jan 02 15:04:05 -0700 2006"
	t, err := time.Parse(timeFmt, s)
	if err != nil {
		panic(err)
	}
	return t.Unix()
}

func main() {
	var countryCode string
	var searchExpr string
	var userLocationExpr string
	flag.StringVar(&countryCode, "country", "", "country code")
	flag.StringVar(&userLocationExpr, "userlocationexpr", ".*", "user location expression")
	flag.StringVar(&searchExpr, "searchexpr", ".*", "search expression")
	flag.Parse()
	tm := &TweetMunger{
		CountryCode: strings.ToUpper(countryCode),
		SearchExpr: regexp.MustCompile(searchExpr),
		UserLocationExpr: regexp.MustCompile(userLocationExpr),
		Writer: csv.NewWriter(os.Stdout),
	}
	tm.Writer.Write([]string{
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

	tarFile, err := os.Open(args[0])
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
			break;
		} else if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		if !strings.HasSuffix(hdr.Name, ".json.bz2") {
			continue
		}

		_, err = io.Copy(&b, tr)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		bzipReader := bzip2.NewReader(&b)
		s := bufio.NewScanner(bzipReader)
		
		for s.Scan() {
			line := s.Text()
			if len(line) == 0 {
				continue
			}
			tweet, err := tm.processLine(line)
			if err != nil {
				continue
			}
			if tweet.ID == 0 {
				continue
			}
			tm.toCSV(tweet)
		}
	}
}

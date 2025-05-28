package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
)

const (
	StatusCheckSeconds = 30
	PlacedStatus       = "Order Placed"
	PreparingStatus    = "Preparing Your Order"
	ArrivedStatus      = "Order Arrived"
)

func checkLunchTime() string {
	now := time.Now()
	if now.Hour() < 11 || (now.Hour() == 11 && now.Minute() < 30) {
		return "EARLY"
	} else if now.Hour() >= 12 {
		return "LATE"
	} else {
		return "ON-TIME"
	}
}

func checkOrderStatus(page *rod.Page) (string, error) {
	elem := page.Timeout(10 * time.Second).Element(".schedule-card-label")
	if elem == nil {
		return "", fmt.Errorf("status label not found")
	}
	status, err := elem.Text()
	if err != nil {
		return "", err
	}
	return status, nil
}

func loginRelish(page *rod.Page, email, password string) error {
	page.MustNavigate("https://relish.ezcater.com/schedule")
	time.Sleep(5 * time.Second)

	username := page.MustElement("#identity_email")
	username.MustInput(email)
	page.MustElement(`input[name="commit"]`).MustClick()

	page.Timeout(10 * time.Second).MustElement("#password").MustInput(password)
	page.MustElement(`input[name="action"]`).MustClick()

	time.Sleep(5 * time.Second)
	page.MustNavigate("https://relish.ezcater.com/schedule")
	return nil
}

func main() {
	email := os.Getenv("RELISH_EMAIL")
	password := os.Getenv("RELISH_PASSWORD")
	if email == "" || password == "" {
		log.Fatal("Please set RELISH_EMAIL and RELISH_PASSWORD environment variables")
	}

	// Launch headless Chrome
	url := launcher.New().Headless(true).MustLaunch()
	browser := rod.New().ControlURL(url).MustConnect()
	defer browser.MustClose()

	page := browser.MustPage()

	// Login to Relish
	fmt.Println("Logging into Relish...")
	err := loginRelish(page, email, password)
	if err != nil {
		log.Fatalf("Failed to log in: %v", err)
	}

	fmt.Println("Begin lunch status checking...")
	ctx := context.Background()

	for {
		select {
		case <-ctx.Done():
			fmt.Println("Context cancelled, exiting.")
			return
		default:
			lunchTime := checkLunchTime()
			switch lunchTime {
			case "EARLY":
				fmt.Println("Checking Relish, but it's a little early for lunch... someone is hungry!")
			case "LATE":
				fmt.Println("Checking Relish, but it's a little late for lunch... might wanna talk to Shawn!")
			case "ON-TIME":
				// pass
			default:
				log.Fatal("UNRECOGNIZED LUNCH TIME - PLEASE ENSURE THE SPACE-TIME CONTINUUM IS INTACT")
			}

			status, err := checkOrderStatus(page)
			if err != nil {
				log.Printf("Error checking status: %v", err)
			} else {
				fmt.Printf("CURRENT RELISH STATUS REPORTS AS: '%s'\n", status)
				if strings.Contains(status, ArrivedStatus) {
					fmt.Println("Order has arrived!")
					// sendSlack() -- implement as needed
					return
				}
			}
			fmt.Printf("Checking again in %d seconds...\n", StatusCheckSeconds)
			page.MustReload()
			time.Sleep(StatusCheckSeconds * time.Second)
		}
	}
}

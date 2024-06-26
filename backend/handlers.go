package main

import (
	"context"
	"encoding/json"
	"io"
	"log"
	"net/http"

	"cloud.google.com/go/speech/apiv1"
	"cloud.google.com/go/speech/apiv1/speechpb"
)

type TranscriptionResponse struct {
	Transcription string `json:"transcription"`
}

func home(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Hello from Say Chess!"))
}

func recognizeMove(w http.ResponseWriter, r *http.Request) {
	audioData, err := io.ReadAll(r.Body)
	if err != nil {
		log.Printf("Error reading audio data: %v", err)
		http.Error(w, "Unable to read audio data", http.StatusBadRequest)
		return
	}

	// Google Cloud setup
	ctx := context.Background()
	client, err := speech.NewClient(ctx)
	if err != nil {
		log.Printf("Error creating Google Cloud Speech client: %v", err)
		http.Error(w, "Failed to create client", http.StatusInternalServerError)
		return
	}
	defer client.Close()

	req := &speechpb.RecognizeRequest{
		Config: &speechpb.RecognitionConfig{
			Encoding:        speechpb.RecognitionConfig_LINEAR16,
			SampleRateHertz: 16000,
			LanguageCode:    "en-US",
		},
		Audio: &speechpb.RecognitionAudio{
			AudioSource: &speechpb.RecognitionAudio_Content{Content: audioData},
		},
	}

	resp, err := client.Recognize(ctx, req)
	if err != nil {
		log.Printf("Error transcribing audio: %v", err)
		http.Error(w, "Failed to transcribe audio", http.StatusInternalServerError)
		return
	}

	if len(resp.Results) == 0 {
		log.Println("No transcription result found")
		http.Error(w, "No transcription result", http.StatusInternalServerError)
		return
	}

	transcription := resp.Results[0].Alternatives[0].Transcript

	response := TranscriptionResponse{Transcription: transcription}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

import "./style.css";
import { startRecording, stopRecording, playAudio } from "./recorder.js";

document.querySelector("#app").innerHTML = `
  <div>
    <button id="start-record">Start Recording</button>
    <button id="stop-record">Stop Recording</button>
  </div>
`;

const startButton = document.querySelector("#start-record");
startButton.onclick = startRecording;

const stopButton = document.querySelector("#stop-record");
stopButton.onclick = async () => {
  const wavAudioBlob = await stopRecording();
  const formData = new FormData();
  formData.append("file", wavAudioBlob, "file.wav");
  const apiUrl = "http://localhost:5000/speech/transcribe-move";

  const response = await fetch(apiUrl, {
    method: "POST",
    cache: "no-cache",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      `HTTP error! status: ${response.status}, response: ${errorText}`,
    );
  }

  console.log(response.json());
};

import { MediaRecorder, register } from "extendable-media-recorder";
import { connect } from "extendable-media-recorder-wav-encoder";

let mediaRecorder = null;
let audioBlobs = [];
let capturedStream = null;

await register(await connect());

export const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
      },
    });
    audioBlobs = [];
    capturedStream = stream;

    mediaRecorder = new MediaRecorder(stream, {
      mimeType: "audio/wav",
    });

    mediaRecorder.addEventListener("dataavailable", (event) => {
      audioBlobs.push(event.data);
    });
    mediaRecorder.start();
  } catch (e) {
    console.error(e);
  }
};

export const stopRecording = () => {
  return new Promise((resolve) => {
    if (!mediaRecorder) {
      resolve(null);
      return;
    }

    mediaRecorder.addEventListener("stop", () => {
      const mimeType = mediaRecorder.mimeType;
      const audioBlob = new Blob(audioBlobs, { type: mimeType });

      if (capturedStream) {
        capturedStream.getTracks().forEach((track) => track.stop());
      }

      resolve(audioBlob);
    });
    mediaRecorder.stop();
  });
};

export const playAudio = (audioBlob) => {
  if (audioBlob) {
    const audio = new Audio();
    audio.src = URL.createObjectURL(audioBlob);
    audio.play();
  }
};

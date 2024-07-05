import { useReactMediaRecorder } from "react-media-recorder";

const RecorderButton = () => {
  const { status, startRecording, stopRecording } = useReactMediaRecorder({
    audio: {
      channelCount: 1,
      echoCancellation: true,
    },
    onStop: (blobUrl, _) => {
      getMoveFromAudio(blobUrl);
    },
  });

  const getMoveFromAudio = async (mediaBlobUrl: string) => {
    const apiUrl = import.meta.env.VITE_API_URL + "/speech/transcribe-move";

    const audioResponse = await fetch(mediaBlobUrl);
    const blob = await audioResponse.blob();

    const formData = new FormData();
    formData.append("file", blob, "file.wav");

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

  return (
    <>
      <button onClick={status === "recording" ? stopRecording : startRecording}>
        {status === "stopped" || status === "idle"
          ? "Start Recording"
          : "Submit"}
      </button>
    </>
  );
};

export default RecorderButton;

import { useEffect, useRef, useState } from "react";
import { Chessboard } from "react-chessboard";
import { useParams } from "react-router-dom";
import { useReactMediaRecorder } from "react-media-recorder";

const Game = () => {
  const apiUrl = import.meta.env.VITE_API_URL;
  const params = useParams<{ gameId: string }>();
  const [fen, setFen] = useState<string>();
  const [curPlayer, setCurPlayer] = useState<"w" | "b">("w");
  const fenRef = useRef<string | undefined>();
  const [loading, setLoading] = useState<boolean>(true);
  const [gameStatus, setGameStatus] = useState<string>("");
  const [move, setMove] = useState<string>("");

  const getMoveFromAudio = async (mediaBlobUrl: string, fen: string) => {
    const url = apiUrl + "/speech/transcribe-move";

    const audioResponse = await fetch(mediaBlobUrl);
    const blob = await audioResponse.blob();

    const formData = new FormData();
    formData.append("file", blob, "file.wav");
    formData.append("fen", fen);

    const response = await fetch(url, {
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
    // console.log(response.json());
    return response.json();
  };

  const makeMove = async (move: string) => {
    const url = apiUrl + `/game/${params.gameId}/move`;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-cache",
      body: JSON.stringify({
        move: move,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `HTTP error! status: ${response.status}, response: ${errorText}`,
      );
    }

    const json = await response.json();
    setFen(json.data.fen);
    setGameStatus(json.data.game_status);
    setCurPlayer(json.data.fen.split(" ")[1]);
    setMove("");
  };

  const { status, startRecording, stopRecording } = useReactMediaRecorder({
    audio: {
      channelCount: 1,
      echoCancellation: true,
    },
    onStop: async (blobUrl, _) => {
      if (fenRef.current) {
        const responseJson = await getMoveFromAudio(blobUrl, fenRef.current);
        setMove(responseJson.data.san_move);
      } else {
        console.error("FEN is not available!");
      }
    },
  });

  useEffect(() => {
    setLoading(true);
    const fetchFen = async () => {
      const response = await fetch(apiUrl + `/game/${params.gameId}`);
      const gameJson = await response.json();
      setFen(gameJson.data.fen);
      setGameStatus(gameJson.data.game_status);
      setCurPlayer(gameJson.data.fen.split(" ")[1]);
      setLoading(false);
    };
    fetchFen();
  }, []);

  useEffect(() => {
    fenRef.current = fen;
  }, [fen]);

  return (
    <>
      {loading ? (
        <h1>Loading...</h1>
      ) : (
        <>
          <Chessboard
            position={fen}
            boardWidth={560}
            arePiecesDraggable={false}
          />
          {gameStatus === "ongoing" ? (
            <>
              <button
                onClick={
                  status === "recording" ? stopRecording : startRecording
                }
              >
                {status === "stopped" || status === "idle"
                  ? "Start Recording"
                  : "Submit"}
              </button>
              <div>
                {move !== "" && (
                  <div>
                    <h1>{move}</h1>
                    <button
                      onClick={() => {
                        makeMove(move);
                      }}
                    >
                      Confirm
                    </button>
                    <button
                      onClick={() => {
                        setMove("");
                      }}
                    >
                      Redo
                    </button>
                  </div>
                )}
              </div>
              <div>{curPlayer === "w" ? "White" : "Black"} to move</div>
            </>
          ) : (
            <div>{gameStatus}</div>
          )}
        </>
      )}
    </>
  );
};

export default Game;

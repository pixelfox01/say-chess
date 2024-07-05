import { Chessboard } from "react-chessboard";
import RecorderButton from "./recorderButton";

function App() {
  return (
    <>
      <Chessboard id="ChessBoard" boardWidth={680} arePiecesDraggable={false} />
      <RecorderButton />
    </>
  );
}

export default App;

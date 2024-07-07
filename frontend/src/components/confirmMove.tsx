type ConfirmMoveProps = {
  san_move: string;
};
const ConfirmMove = (props: ConfirmMoveProps) => {
  return (
    <div>
      <h1>{props.san_move}</h1>
      <button></button>
    </div>
  );
};

export default ConfirmMove;

import { FormEvent, useState } from "react";
import { Link, redirect, useNavigate } from "react-router-dom";

const Home = () => {
  const apiUrl = import.meta.env.VITE_API_URL + "/game";
  const navigate = useNavigate();
  const startGame = async () => {
    const response = await fetch(apiUrl + "/start", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        player1_id: 1,
        player2_id: null,
      }),
    });
    if (!response.ok) {
      const errorJson = await response.json();
      if (errorJson.error.code === 1001) {
        navigate(`/game/${errorJson.error.data.player1_game}`);
      } else {
        throw new Error(
          `HTTP error! status: ${response.status}, response: ${JSON.stringify(errorJson)}`,
        );
      }
    } else {
      const result = await response.json();
      navigate(`/game/${result.data}`);
    }
  };
  return (
    <div>
      <button onClick={startGame}>Start Game</button>
    </div>
  );
};

export default Home;

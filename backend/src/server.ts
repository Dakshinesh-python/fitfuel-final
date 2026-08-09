import "dotenv/config";
import { createApp } from "./app";

const PORT = process.env.PORT ? Number(process.env.PORT) : 4000;

const app = createApp();

app.listen(PORT, () => {
  console.log(`FitFuel backend running on port ${PORT}`);
});

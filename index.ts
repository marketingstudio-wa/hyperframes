// Seedance 2.5 text-to-video example using the official Higgsfield SDK.
// Run with `bun index.ts`. Bun loads HF_CREDENTIALS (key-id:key-secret) from
// .env.local or the process environment; the value is never printed.
import { config, higgsfield, HiggsfieldError } from "@higgsfield/client/v2";

const MODEL = "bytedance/seedance-2.5/text-to-video";

const credentials = process.env.HF_CREDENTIALS;
if (!credentials) {
  console.error(
    "HF_CREDENTIALS is not set. Add it to .env.local or the environment as key-id:key-secret.",
  );
  process.exit(1);
}

config({ credentials });

try {
  const result = await higgsfield.subscribe(MODEL, {
    input: {
      prompt: "A cinematic scene at sunset",
      duration: 5,
      resolution: "720p",
      aspect_ratio: "16:9",
    },
    withPolling: true,
  });

  // The API reports "nsfw" for moderated requests and "failed" for errors;
  // anything other than "completed" (including a canceled request) is a failure.
  const status: string = result.status;
  if (status !== "completed") {
    const reason =
      status === "nsfw"
        ? "rejected by moderation"
        : status === "failed"
          ? "generation failed"
          : `ended with status "${status}"`;
    console.error(`Request ${result.request_id} ${reason}. No video was produced.`);
    process.exit(1);
  }

  const url = result.video?.url;
  if (!url) {
    console.error(`Request ${result.request_id} completed but returned no video URL.`);
    process.exit(1);
  }

  console.log(`Request ${result.request_id} completed.`);
  console.log(`Video URL: ${url}`);
} catch (error) {
  const message =
    error instanceof HiggsfieldError ? `${error.name}: ${error.message}` : String(error);
  console.error(`Higgsfield request failed. ${message}`);
  process.exit(1);
}

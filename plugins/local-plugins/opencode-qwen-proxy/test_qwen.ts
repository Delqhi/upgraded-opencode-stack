import { generatePKCE, requestDeviceAuthorization } from "./src/qwen/oauth.ts";
async function main() {
  const { verifier, challenge } = generatePKCE();
  console.log("Challenge:", challenge);
  try {
    const res = await requestDeviceAuthorization(challenge);
    console.log("Result:", res);
  } catch (e) {
    console.error("Error:", e);
  }
}
main();

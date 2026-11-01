// Google sign-in through Firebase. Firebase only proves who the person is: the ID token goes to the API, which returns
// a normal BrandGuard session, so nothing else in the app talks to Firebase.
import type { Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "",
};

export const firebaseConfigured = Boolean(firebaseConfig.apiKey && firebaseConfig.authDomain && firebaseConfig.projectId);

type FirebaseAuth = { auth: Auth; sdk: typeof import("firebase/auth") };
type PopupResolver = { _initialize?: (auth: Auth) => Promise<unknown> };

/** On desktop Chrome, Firefox and Edge, Firebase only downloads its sign-in iframe (from the authDomain) once
 *  signInWithPopup is called, and opens the window after that finishes. If the download is slow, the browser no longer
 *  counts the click and blocks the popup. Firebase already does this step early on Safari and mobile; there is no
 *  public API for it, so make the same internal call. If a future SDK drops it, sign-in still works as before. */
async function preparePopup(auth: Auth) {
  try {
    await auth.authStateReady();
    const resolver = (auth as unknown as { _popupRedirectResolver?: PopupResolver })._popupRedirectResolver;
    await resolver?._initialize?.(auth);
  } catch {
    /* not fatal: signInWithPopup will try again on the click */
  }
}
let ready: FirebaseAuth | null = null;
let pending: Promise<FirebaseAuth> | null = null;

/** Get everything ready before the click. A browser only allows a popup opened directly by a click, so no network
 *  work may happen between the click and the window opening: call this as soon as the Google button is shown. */
export function loadFirebase(): Promise<FirebaseAuth> {
  pending ??= Promise.all([import("firebase/app"), import("firebase/auth")])
    .then(async ([appSdk, sdk]) => {
      const app = appSdk.getApps()[0] ?? appSdk.initializeApp(firebaseConfig);
      const auth = sdk.getAuth(app);
      await preparePopup(auth);
      ready = { auth, sdk };
      return ready;
    })
    .catch((e) => {
      pending = null; // let a later call try again
      throw e;
    });
  return pending;
}

const MESSAGES: Record<string, string> = {
  "auth/popup-blocked": "Your browser blocked the Google sign-in window. Allow pop-ups for this site and try again.",
  "auth/unauthorized-domain": "Google sign-in isn't allowed on this domain yet. Add it in Firebase under Authentication > Settings > Authorized domains.",
  "auth/operation-not-allowed": "Google sign-in is switched off in Firebase. Turn it on under Authentication > Sign-in method.",
  "auth/network-request-failed": "Couldn't reach Google. Check your connection and try again.",
};

/** Show the Google account picker and return a Firebase ID token, or null if the person closed it. */
export async function signInWithGooglePopup(): Promise<string | null> {
  const wasReady = ready !== null;
  const { auth, sdk } = ready ?? (await loadFirebase()); // already loaded in the normal case, so the popup is allowed
  const provider = new sdk.GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  try {
    const result = await sdk.signInWithPopup(auth, provider);
    const idToken = await result.user.getIdToken();
    sdk.signOut(auth).catch(() => {}); // BrandGuard keeps its own session; drop Firebase's without waiting for it
    return idToken;
  } catch (e: unknown) {
    const code = (e as { code?: string }).code ?? "";
    if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") return null;
    if (code === "auth/popup-blocked" && !wasReady) {
      // Clicked before Firebase was ready, so it finished preparing first and the browser no longer counted the
      // click. It is ready now, so the next click opens the popup straight away.
      throw new Error("Google sign-in needed a moment to get ready. Click Continue with Google again.");
    }
    throw new Error(MESSAGES[code] ?? "Google sign-in failed. Please try again.");
  }
}

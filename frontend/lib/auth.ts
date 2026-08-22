export function getToken(): string | null {

  if (
    typeof window === "undefined"
  ) {
    return null;
  }

  return localStorage.getItem(
    "hex_token"
  );
}


export function setToken(
  token: string
) {

  localStorage.setItem(
    "hex_token",
    token
  );
}


export function clearToken() {

  localStorage.removeItem(
    "hex_token"
  );
}


export function isAuthenticated():
  boolean {

  return Boolean(
    getToken()
  );
}
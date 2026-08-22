const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";


export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {

  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("hex_token")
      : null;


  const headers = new Headers(
    options.headers,
  );


  if (!headers.has("Content-Type")) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }


  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }


  const url =
    `${API_BASE_URL}${endpoint}`;


  try {

    const response = await fetch(
      url,
      {
        ...options,
        headers,
      },
    );


    if (response.status === 401) {

      if (
        typeof window !== "undefined"
      ) {

        localStorage.removeItem(
          "hex_token",
        );

        window.location.href =
          "/login";
      }

      throw new Error(
        "Session expired. Please login again.",
      );
    }


    if (!response.ok) {

      let message =
        `Request failed (${response.status})`;


      try {

        const error =
          await response.json();


        if (
          typeof error?.detail ===
          "string"
        ) {
          message =
            error.detail;
        }

      } catch {
        // Keep default message.
      }


      throw new Error(
        message,
      );
    }


    const contentType =
      response.headers.get(
        "content-type",
      );


    if (
      contentType?.includes(
        "application/json",
      )
    ) {

      return (
        await response.json()
      ) as T;

    }


    return (
      (await response.text()) as T
    );

  } catch (error) {

    console.error(
      "[HEX API]",
      {
        url,
        error,
      },
    );

    throw error;
  }
}
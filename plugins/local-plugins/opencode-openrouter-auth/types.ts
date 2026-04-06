export interface OpenRouterCredentials {
  accessToken: string;
  refreshToken: string;
  expiryDate?: number; // Unix timestamp in milliseconds
  createdAt?: number; // Unix timestamp in milliseconds
}

export interface OpenRouterAuthConfig {
  clientId: string;
  redirectUri: string;
  scope: string;
  authorizationEndpoint: string;
  tokenEndpoint: string;
}

export interface OpenRouterTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}
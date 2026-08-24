import api from "./client";
import type {
  UserRegister,
  UserLogin,
  UserResponse,
  TokenResponse,
  UserUpdate,
  PasswordChange,
} from "../types";

export const authApi = {
  register: (data: UserRegister) =>
    api.post<UserResponse>("/api/auth/register", data).then((r) => r.data),

  login: (data: UserLogin) =>
    api.post<TokenResponse>("/api/auth/login", data).then((r) => r.data),

  oauthToken: (formData: FormData) =>
    api
      .post<TokenResponse>("/api/auth/token", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      .then((r) => r.data),

  refresh: (refreshToken: string) =>
    api
      .post<TokenResponse>("/api/auth/refresh", { refresh_token: refreshToken })
      .then((r) => r.data),

  me: () =>
    api.get<UserResponse>("/api/auth/me").then((r) => r.data),
};

export const profileApi = {
  get: () =>
    api.get<UserResponse>("/api/profile/").then((r) => r.data),

  update: (data: UserUpdate) =>
    api.put<UserResponse>("/api/profile/", data).then((r) => r.data),

  changePassword: (data: PasswordChange) =>
    api.put("/api/profile/password", data).then((r) => r.data),

  delete: () =>
    api.delete("/api/profile/").then((r) => r.data),
};

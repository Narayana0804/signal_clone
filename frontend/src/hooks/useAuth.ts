"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest, ApiError } from "@/lib/api";
import { useAppStore } from "@/stores/appStore";
import { User, AuthResponse } from "@/types";


export function useAuth() {
  const currentUser = useAppStore((state) => state.currentUser);
  const setCurrentUser = useAppStore((state) => state.setCurrentUser);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMe = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const user = await apiRequest<User>("/auth/me");
      setCurrentUser(user);
      return user;
    } catch (err) {
      setCurrentUser(null);
      if (err instanceof ApiError && err.status !== 401) {
        setError(err.message);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [setCurrentUser]);

  useEffect(() => {
    fetchMe();
  }, [fetchMe]);

  const register = async (phoneNumber: string, displayName: string) => {
    setError(null);
    try {
      const user = await apiRequest<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          phone_number: phoneNumber,
          display_name: displayName,
        }),
      });
      return user;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Registration failed");
      }
      throw err;
    }
  };

  const verifyOtp = async (phoneNumber: string, otp: string) => {
    setError(null);
    try {
      const result = await apiRequest<{ verified: boolean }>("/auth/verify", {
        method: "POST",
        body: JSON.stringify({
          phone_number: phoneNumber,
          otp,
        }),
      });
      return result;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Verification failed");
      }
      throw err;
    }
  };

  const login = async (phoneNumber: string, otp: string) => {
    setError(null);
    try {
      const data = await apiRequest<{ user: User; token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          phone_number: phoneNumber,
          otp,
        }),
      });
      setCurrentUser(data.user);
      return data;
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Login failed");
      }
      throw err;
    }
  };

  const logout = async () => {
    try {
      await apiRequest("/auth/logout", { method: "POST" });
    } catch {
      // Ignore network errors on logout
    } finally {
      setCurrentUser(null);
    }
  };

  return {
    currentUser,
    loading,
    error,
    register,
    verifyOtp,
    login,
    logout,
    fetchMe,
  };
}

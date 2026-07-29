import React, { createContext, useContext, useReducer } from "react";

const AlertsContext = createContext(null);

const initialState = {
  alerts: [],
  status: "idle", // "idle" | "loading" | "loaded" | "error"
  error: null,
  filters: { threatType: "all", severity: "all" },
};

function reducer(state, action) {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, status: "loading", error: null };
    case "FETCH_SUCCESS":
      return { ...state, status: "loaded", alerts: action.alerts, error: null };
    case "FETCH_ERROR":
      return { ...state, status: "error", error: action.error };
    case "SET_FILTER":
      return { ...state, filters: { ...state.filters, [action.key]: action.value } };
    case "ADD_ALERT":
      return { ...state, alerts: [action.alert, ...state.alerts] };
    case "REMOVE_ALERT":
      return { ...state, alerts: state.alerts.filter((a) => a.id !== action.id) };
    default:
      return state;
  }
}

export function AlertsProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return <AlertsContext.Provider value={{ ...state, dispatch }}>{children}</AlertsContext.Provider>;
}

export function useAlerts() {
  const ctx = useContext(AlertsContext);
  if (!ctx) {
    throw new Error("useAlerts must be used within an AlertsProvider");
  }
  return ctx;
}

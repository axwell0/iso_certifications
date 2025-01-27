import { useCallback } from "react";
import { toast as toastify } from "react-toastify";

export const useToast = () => {
  const toast = useCallback(({ title, description, variant }) => {
    toastify(description, {
      type: variant === "destructive" ? "error" : "success",
      position: "top-right",
      autoClose: 5000,
      hideProgressBar: false,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
    });
  }, []);

  return { toast };
};

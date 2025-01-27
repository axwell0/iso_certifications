// src/components/Layout/GlobalLoading.tsx
import { useNavigation } from "react-router-dom";
import { LoadingSpinner } from "./LoadingSpinner";

export const GlobalLoading = () => {
  const navigation = useNavigation();

  return (
    <>
      {navigation.state !== "idle" && <LoadingSpinner />}
    </>
  );
};
// Plain-English description: Landing page that redirects users to the login screen.

import { useEffect } from "react";
import { useRouter } from "next/router";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/login");
  }, [router]);

  return (
    <div>
      <p>Redirecting to login...</p>
    </div>
  );
}


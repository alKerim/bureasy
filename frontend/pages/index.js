// pages/index.js
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4 flex flex-col items-center justify-center">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-lg p-8 text-gray-800">
        <h1 className="text-4xl font-bold mb-4 text-center text-blue-600">Welcome to BUREASY</h1>
        <p className="text-lg mb-8 text-center">
          Your one-stop solution for navigating bureaucratic tasks. Whether it’s renewing a visa, getting a driver’s license, or any other government service—we simplify every step.
        </p>

        <div className="flex justify-center">
        <Link
            href="/assistant-response"
            className="inline-block px-6 py-3 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition"
          >
            Get Started
        </Link>

        </div>

        <div className="mt-8 text-center text-gray-600">
          <p>Have questions? Just click “Get Started” and ask away!</p>
        </div>
      </div>
    </div>
  );
}

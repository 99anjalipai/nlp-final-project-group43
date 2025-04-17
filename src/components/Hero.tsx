
import { Video } from "lucide-react";

export const Hero = () => {
  return (
    <div className="text-center py-10">
      <div className="inline-block p-3 bg-indigo-100 rounded-full mb-4">
        <Video size={32} className="text-indigo-600" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl mb-4">
        Video<span className="text-indigo-600">Verse</span>
      </h1>
      <p className="text-xl text-gray-600 max-w-2xl mx-auto">
        Transform any video into concise text summaries with our advanced NLP model.
        Just paste an MP4 link and get the key points in seconds.
      </p>
    </div>
  );
};

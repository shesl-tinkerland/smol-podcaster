"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { chapterApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/sidebar";

export default function SyncPage() {
  const [videoName, setVideoName] = useState("");
  const [audioName, setAudioName] = useState("");
  const [chapters, setChapters] = useState("");

  const syncChaptersMutation = useMutation({
    mutationFn: () =>
      chapterApi.sync({
        video_name: videoName,
        audio_name: audioName,
        chapters,
      }),
    onSuccess: () => {
      // Reset form
      setVideoName("");
      setAudioName("");
      setChapters("");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoName || !audioName || !chapters) return;
    syncChaptersMutation.mutate();
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-4xl">
          <h2 className="text-3xl font-bold mb-6">Sync Video Chapters</h2>
          
          {syncChaptersMutation.isSuccess && (
            <div className="mb-6 p-4 bg-green-800 text-green-200 rounded-lg">
              Syncing chapters for {videoName} and {audioName}
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Chapter Synchronization</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="video_name">Video File Name</Label>
                  <Input
                    id="video_name"
                    type="text"
                    value={videoName}
                    onChange={(e) => setVideoName(e.target.value)}
                    className="mt-2"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="audio_name">Audio File Name</Label>
                  <Input
                    id="audio_name"
                    type="text"
                    value={audioName}
                    onChange={(e) => setAudioName(e.target.value)}
                    className="mt-2"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="chapters">Chapters</Label>
                  <Textarea
                    id="chapters"
                    value={chapters}
                    onChange={(e) => setChapters(e.target.value)}
                    className="mt-2 min-h-[200px]"
                    placeholder="[00:00:00] Introduction&#10;[00:05:30] Main Topic&#10;..."
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={!videoName || !audioName || !chapters || syncChaptersMutation.isPending}
                >
                  {syncChaptersMutation.isPending ? "Syncing..." : "Sync Chapters"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
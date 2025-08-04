"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { episodeApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sidebar } from "@/components/sidebar";
import { Upload } from "lucide-react";

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [speakersCount, setSpeakersCount] = useState("2");
  const [transcriptOnly, setTranscriptOnly] = useState(false);
  const [generateExtra, setGenerateExtra] = useState(false);

  const queryClient = useQueryClient();

  const createEpisodeMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("speakers_count", speakersCount);
      formData.append("transcript_only", transcriptOnly.toString());
      formData.append("generate_extra", generateExtra.toString());
      
      if (file) {
        formData.append("file", file);
      } else if (url) {
        formData.append("url", url);
      }

      return episodeApi.create(formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["episodes"] });
      // Reset form
      setFile(null);
      setUrl("");
      setName("");
      setSpeakersCount("2");
      setTranscriptOnly(false);
      setGenerateExtra(false);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((!file && !url) || !name) return;
    createEpisodeMutation.mutate();
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-4xl">
          <h2 className="text-3xl font-bold mb-6">Create Writeup</h2>
          
          {createEpisodeMutation.isSuccess && (
            <div className="mb-6 p-4 bg-green-800 text-green-200 rounded-lg">
              Processing started for {name}
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>New Episode</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="file">Audio File</Label>
                    <div className="mt-2">
                      <label
                        htmlFor="file"
                        className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:border-primary transition-colors"
                      >
                        <Upload className="w-8 h-8 text-gray-400 mb-2" />
                        <span className="text-sm text-gray-400">
                          {file ? file.name : "Drop audio file or click to upload"}
                        </span>
                        <input
                          id="file"
                          type="file"
                          className="hidden"
                          accept="audio/*"
                          onChange={(e) => setFile(e.target.files?.[0] || null)}
                        />
                      </label>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-gray-400">or</span>
                    <div className="flex-1">
                      <Label htmlFor="url">URL</Label>
                      <Input
                        id="url"
                        type="url"
                        placeholder="Enter URL"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        className="mt-2"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="speakers">Number of Speakers</Label>
                      <Input
                        id="speakers"
                        type="number"
                        min="1"
                        value={speakersCount}
                        onChange={(e) => setSpeakersCount(e.target.value)}
                        className="mt-2"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="name">Episode Name</Label>
                      <Input
                        id="name"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="mt-2"
                        required
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="transcript-only"
                        checked={transcriptOnly}
                        onCheckedChange={(checked) => setTranscriptOnly(checked as boolean)}
                      />
                      <Label htmlFor="transcript-only" className="cursor-pointer">
                        Transcript Only
                      </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="generate-extra"
                        checked={generateExtra}
                        onCheckedChange={(checked) => setGenerateExtra(checked as boolean)}
                      />
                      <Label htmlFor="generate-extra" className="cursor-pointer">
                        Generate titles and tweets
                      </Label>
                    </div>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={(!file && !url) || !name || createEpisodeMutation.isPending}
                >
                  {createEpisodeMutation.isPending ? "Processing..." : "Create Artifacts"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
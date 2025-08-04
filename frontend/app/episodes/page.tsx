"use client";

import { useQuery } from "@tanstack/react-query";
import { episodeApi } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Sidebar } from "@/components/sidebar";
import { format } from "date-fns";
import Link from "next/link";
import { ProcessingStatus } from "@/types";
import { Badge } from "@/components/ui/badge";

export default function EpisodesPage() {
  const { data: episodes, isLoading } = useQuery({
    queryKey: ["episodes"],
    queryFn: episodeApi.list,
  });

  const getStatusBadge = (status: ProcessingStatus) => {
    const variants: Record<ProcessingStatus, { variant: "default" | "secondary" | "destructive" | "outline"; text: string }> = {
      [ProcessingStatus.PENDING]: { variant: "secondary", text: "Pending" },
      [ProcessingStatus.PROCESSING]: { variant: "outline", text: "Processing" },
      [ProcessingStatus.COMPLETED]: { variant: "default", text: "Completed" },
      [ProcessingStatus.FAILED]: { variant: "destructive", text: "Failed" },
    };
    
    const { variant, text } = variants[status];
    return <Badge variant={variant}>{text}</Badge>;
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl">
          <h2 className="text-3xl font-bold mb-6">Edit Episodes</h2>

          {isLoading ? (
            <div className="text-center py-8">Loading episodes...</div>
          ) : episodes && episodes.length > 0 ? (
            <div className="space-y-4">
              {episodes.map((episode) => (
                <Card key={episode.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-muted-foreground">
                        {format(new Date(episode.created_at), "MMM d")}
                      </span>
                      <div>
                        <h3 className="font-medium">{episode.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {episode.speakers_count} speakers
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      {getStatusBadge(episode.status)}
                      {episode.status === ProcessingStatus.COMPLETED && (
                        <Link
                          href={`/episodes/${episode.id}/edit`}
                          className="text-primary hover:underline"
                        >
                          Edit Show Notes
                        </Link>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No episodes found.</p>
          )}
        </div>
      </main>
    </div>
  );
}
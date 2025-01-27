import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, ArrowRight, ExternalLink, MessageCircle } from 'lucide-react';

import Layout from '../components/Layout/Layout';
import Header from '../components/Layout/Header';
import { Input } from '../components/ui/input';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { fetchWithAuth } from '../utils/api';
import { useUserProfileContext } from '../context/UserProfileContext';
import { useToast } from '@/hooks/useToast';

interface Standard {
  Iso: string;
  Category: string;
  SubCategory: string;
  description: string;
  edition: string;
  number_of_pages: string;
  stage: string;
  technical_committee: string;
  url: string;
  publication_date: string;
}

const ITEMS_PER_PAGE = 10;

const Standards: React.FC = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const { userProfile } = useUserProfileContext();

  const [searchQuery, setSearchQuery] = useState('');
  const [standards, setStandards] = useState<Standard[]>([]);
  const [selectedStandard, setSelectedStandard] = useState<Standard | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [categories, setCategories] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    const fetchData = async () => {
      setIsLoading(true);
      try {
        await fetchStandards(controller.signal);
      } finally {
        setIsLoading(false);
      }
    };

    const timeoutId = setTimeout(fetchData, 300);
    return () => {
      controller.abort();
      clearTimeout(timeoutId);
    };
  }, [searchQuery, currentPage, categoryFilter]);

  useEffect(() => {
    const uniqueCategories = Array.from(new Set(standards.map((standard) => standard.Category))).sort();
    setCategories(uniqueCategories);
  }, [standards]);

  const fetchStandards = async (signal?: AbortSignal) => {
    try {
      const params = new URLSearchParams({
        keyword: searchQuery,
        offset: String((currentPage - 1) * ITEMS_PER_PAGE),
        limit: String(ITEMS_PER_PAGE),
        category: categoryFilter,
      });

      const response = await fetchWithAuth(`/standards/?${params.toString()}`, {
        signal,
        method: 'GET',
      });

      if (!response.ok) throw new Error('Failed to fetch standards');

      const responseData = await response.json();
      const data = Array.isArray(responseData) ? responseData : responseData.data || [];
      const totalCountHeader = response.headers.get('X-Total-Count');
      let totalCount = totalCountHeader ? parseInt(totalCountHeader, 10) : 0;

      if (!totalCount && responseData.total) totalCount = responseData.total;

      setStandards(data);
      setTotalPages(Math.ceil(totalCount / ITEMS_PER_PAGE) || 1);
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        console.error('Fetch error:', error);
        setStandards([]);
        toast({
          title: 'Error',
          description: 'Failed to load standards',
          variant: 'destructive',
        });
      }
    }
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const handleChatNavigation = (iso: string) => {
    navigate('/chat', {
      state: { initialMessage: `Tell me about ${iso}` },
      replace: true
    });
  };

  return (
    <Layout role={userProfile?.role || 'GUEST'}>
      <div className="space-y-6">
        <Header userName={userProfile?.name} />

        <div className="flex flex-wrap gap-4">
          <Input
            placeholder="Search standards..."
            value={searchQuery}
            onChange={(e) => {
              setCurrentPage(1);
              setSearchQuery(e.target.value);
            }}
            className="max-w-lg"
          />

          <div className="flex items-center space-x-2">
            <label htmlFor="categoryFilter" className="text-sm font-medium">
              Category:
            </label>
            <select
              id="categoryFilter"
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="border rounded px-2 py-1 text-sm bg-background text-foreground"
            >
              <option value="">All</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {standards.map((standard) => (
                <div
                  key={standard.Iso}
                  className="w-full p-4 bg-card rounded-lg shadow-sm border hover:bg-muted/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedStandard(standard)}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-2">
                      <h3 className="font-medium text-foreground">{standard.Iso}</h3>
                      <p className="text-muted-foreground">{standard.Category}</p>
                      <small className="text-sm text-muted-foreground">
                        {standard.SubCategory}
                      </small>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleChatNavigation(standard.Iso);
                      }}
                    >
                      <MessageCircle className="w-4 h-4 mr-2" />
                      Chat
                    </Button>
                  </div>
                </div>
              ))}

              {standards.length === 0 && (
                <p className="text-center text-muted-foreground">No standards found.</p>
              )}
            </div>

            <div className="flex justify-center items-center gap-4 py-4">
              <Button
                variant="outline"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Previous
              </Button>
              <span className="text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages || totalPages === 0}
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </>
        )}

        <Dialog open={!!selectedStandard} onOpenChange={(open) => !open && setSelectedStandard(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedStandard?.Iso}</DialogTitle>
            </DialogHeader>
            {selectedStandard && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">Category</h4>
                  <p className="text-muted-foreground">{selectedStandard.Category}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">Subcategory</h4>
                  <p className="text-muted-foreground">{selectedStandard.SubCategory}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">Edition</h4>
                  <p className="text-muted-foreground">{selectedStandard.edition}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">Pages</h4>
                  <p className="text-muted-foreground">{selectedStandard.number_of_pages}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">Stage</h4>
                  <p className="text-muted-foreground">{selectedStandard.stage}</p>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium text-foreground">Technical Committee</h4>
                  <p className="text-muted-foreground">{selectedStandard.technical_committee}</p>
                </div>
                <div className="col-span-2 space-y-2">
                  <h4 className="font-medium text-foreground">Description</h4>
                  <p className="text-muted-foreground">{selectedStandard.description}</p>
                </div>
                <div className="col-span-2 space-y-2">
                  <h4 className="font-medium text-foreground">Publication Date</h4>
                  <p className="text-muted-foreground">
                    {new Date(selectedStandard.publication_date).toLocaleDateString()}
                  </p>
                </div>
                <div className="col-span-2">
                  <Button
                    className="w-full"
                    onClick={() => window.open(selectedStandard.url, '_blank')}
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View Full Standard Document
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
};

export default Standards;
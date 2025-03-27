import React, { useState } from 'react';
import { 
  Box, 
  VStack, 
  HStack, 
  Text, 
  Input, 
  Button, 
  FormControl,
  FormLabel,
  Spinner,
  Divider,
  Badge,
  useColorModeValue,
  useToast
} from '@chakra-ui/react';
import { FaSearch, FaCode } from 'react-icons/fa';
import { searchApi, fileApi } from '../services/api';
import { SearchMatch, File } from '../types';

interface CodeSearchProps {
  projectId: string;
  onResultSelect: (file: File) => void;
}

const CodeSearch: React.FC<CodeSearchProps> = ({ projectId, onResultSelect }) => {
  const [query, setQuery] = useState('');
  const [filePattern, setFilePattern] = useState('');
  const [results, setResults] = useState<SearchMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const toast = useToast();
  
  const bgHover = useColorModeValue('gray.100', 'gray.700');
  const highlightBg = useColorModeValue('yellow.100', 'yellow.800');

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    try {
      setLoading(true);
      setSearched(true);
      
      const response = await searchApi.search(projectId, {
        query,
        file_pattern: filePattern.trim() || undefined,
      });
      
      setResults(response.data.matches);
    } catch (error) {
      console.error('Error searching code:', error);
      toast({
        title: 'Error searching code',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = async (match: SearchMatch) => {
    try {
      const response = await fileApi.getFile(projectId, match.path);
      onResultSelect(response.data);
    } catch (error) {
      console.error('Error fetching file content:', error);
      toast({
        title: 'Error opening file',
        description: 'Could not load file content',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const highlightMatches = (text: string, submatches: SearchMatch['submatches']) => {
    if (!submatches.length) return text;
    
    let result = [];
    let lastIndex = 0;
    
    // Sort submatches by start position
    const sortedMatches = [...submatches].sort((a, b) => a.start - b.start);
    
    for (const match of sortedMatches) {
      // Add text before the match
      if (match.start > lastIndex) {
        result.push(text.substring(lastIndex, match.start));
      }
      
      // Add the highlighted match
      result.push(
        <Box as="span" key={`${match.start}-${match.end}`} bg={highlightBg} fontWeight="bold">
          {text.substring(match.start, match.end)}
        </Box>
      );
      
      lastIndex = match.end;
    }
    
    // Add any remaining text
    if (lastIndex < text.length) {
      result.push(text.substring(lastIndex));
    }
    
    return result;
  };

  return (
    <Box h="100%" display="flex" flexDirection="column">
      <VStack spacing={4} align="stretch" mb={4}>
        <FormControl>
          <FormLabel>Search Query</FormLabel>
          <Input 
            placeholder="Enter search query..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </FormControl>
        
        <FormControl>
          <FormLabel>File Pattern (Optional)</FormLabel>
          <Input 
            placeholder="E.g. *.py, src/*.ts" 
            value={filePattern}
            onChange={(e) => setFilePattern(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </FormControl>
        
        <Button 
          leftIcon={<FaSearch />} 
          colorScheme="brand" 
          onClick={handleSearch}
          isLoading={loading}
          isDisabled={!query.trim()}
        >
          Search
        </Button>
      </VStack>
      
      <Divider mb={4} />
      
      <Box flex="1" overflowY="auto">
        {loading ? (
          <Box textAlign="center" py={8}>
            <Spinner />
            <Text mt={2}>Searching...</Text>
          </Box>
        ) : searched ? (
          results.length === 0 ? (
            <Text textAlign="center" py={4}>No results found</Text>
          ) : (
            <VStack align="stretch" spacing={4}>
              <Text fontWeight="medium">{results.length} results found</Text>
              
              {results.map((match, index) => (
                <Box 
                  key={`${match.path}-${index}`}
                  p={4}
                  borderWidth="1px"
                  borderRadius="md"
                  cursor="pointer"
                  _hover={{ bg: bgHover }}
                  onClick={() => handleResultClick(match)}
                >
                  <HStack mb={2}>
                    <FaCode />
                    <Text fontWeight="bold">{match.path}</Text>
                    <Badge ml="auto">Line {match.line_number}</Badge>
                  </HStack>
                  
                  <Box 
                    p={2} 
                    bg={useColorModeValue('gray.50', 'gray.800')}
                    borderRadius="md"
                    fontFamily="mono"
                    whiteSpace="pre-wrap"
                    fontSize="sm"
                  >
                    {highlightMatches(match.lines, match.submatches)}
                  </Box>
                </Box>
              ))}
            </VStack>
          )
        ) : (
          <Text textAlign="center" color="gray.500">
            Enter a search query and click Search to find code
          </Text>
        )}
      </Box>
    </Box>
  );
};

export default CodeSearch;
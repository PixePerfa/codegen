import React, { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  Heading,
  Input,
  Text,
  VStack,
  HStack,
  Spinner,
  useToast,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Link,
  Code,
  FormControl,
  FormLabel,
  FormHelperText,
  Badge,
} from '@chakra-ui/react';
import { FiSearch, FiFile, FiInfo } from 'react-icons/fi';
import { useApi } from '../services/api';

interface RegexSearchProps {
  projectId: string;
  onFileClick?: (filePath: string, line?: number) => void;
}

interface Match {
  line_number: number;
  line: string;
  match: string;
  start: number;
  end: number;
}

interface FileMatch {
  file_path: string;
  matches: Match[];
}

interface SearchResponse {
  status: string;
  pattern: string;
  file_pattern?: string;
  results: FileMatch[];
  message?: string;
}

const RegexSearch: React.FC<RegexSearchProps> = ({ projectId, onFileClick }) => {
  const toast = useToast();
  const api = useApi();
  const [pattern, setPattern] = useState('');
  const [filePattern, setFilePattern] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);

  const handleSearch = async () => {
    if (!pattern.trim()) {
      toast({
        title: 'Pattern required',
        description: 'Please enter a regex pattern to search for',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.post(`/projects/${projectId}/regex-search`, {
        pattern,
        file_pattern: filePattern.trim() || undefined,
      });
      
      if (response.status === 'success') {
        setSearchResults(response);
      } else {
        throw new Error(response.message || 'Failed to perform regex search');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to perform regex search',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      setSearchResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileClick = (filePath: string, line?: number) => {
    if (onFileClick) {
      onFileClick(filePath, line);
    }
  };

  // Helper function to highlight matched text
  const highlightMatch = (line: string, start: number, end: number) => {
    const before = line.substring(0, start);
    const match = line.substring(start, end);
    const after = line.substring(end);
    
    return (
      <>
        {before}
        <Box as="span" bg="yellow.200" fontWeight="bold">{match}</Box>
        {after}
      </>
    );
  };

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg" bg="white" shadow="sm">
      <Heading size="md" mb={4}>
        Regex Search
      </Heading>
      <Text mb={4}>
        Search the codebase using regular expressions.
      </Text>
      
      <VStack spacing={4} align="stretch" mb={6}>
        <FormControl>
          <FormLabel>Regex Pattern</FormLabel>
          <Input
            placeholder="Enter regex pattern (e.g., 'function\\s+\\w+')"
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <FormHelperText>
            <Flex align="center">
              <FiInfo size="14px" style={{ marginRight: '4px' }} />
              Use standard regex syntax (e.g., \d for digits, \w for word characters)
            </Flex>
          </FormHelperText>
        </FormControl>
        
        <FormControl>
          <FormLabel>File Pattern (Optional)</FormLabel>
          <Input
            placeholder="Limit search to files matching this pattern (e.g., '*.py', 'src/*.ts')"
            value={filePattern}
            onChange={(e) => setFilePattern(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <FormHelperText>
            Use glob patterns like *.py or src/*.ts to filter files
          </FormHelperText>
        </FormControl>
        
        <Button
          leftIcon={<FiSearch />}
          colorScheme="blue"
          onClick={handleSearch}
          isLoading={isLoading}
          loadingText="Searching..."
        >
          Search
        </Button>
      </VStack>

      {isLoading && (
        <Flex justify="center" my={8}>
          <Spinner size="xl" />
        </Flex>
      )}

      {!isLoading && searchResults && (
        <Box>
          <Heading size="sm" mb={3}>
            Results ({searchResults.results.length} files)
          </Heading>

          {searchResults.results.length === 0 ? (
            <Text>No matches found.</Text>
          ) : (
            <Accordion allowMultiple>
              {searchResults.results.map((fileMatch, fileIndex) => (
                <AccordionItem key={fileIndex}>
                  <h2>
                    <AccordionButton>
                      <Box flex="1" textAlign="left">
                        <Flex align="center">
                          <FiFile style={{ marginRight: '8px' }} />
                          <Text fontWeight="medium">{fileMatch.file_path}</Text>
                          <Badge ml={2} colorScheme="blue">{fileMatch.matches.length} matches</Badge>
                        </Flex>
                      </Box>
                      <AccordionIcon />
                    </AccordionButton>
                  </h2>
                  <AccordionPanel pb={4}>
                    <VStack align="stretch" spacing={2}>
                      {fileMatch.matches.map((match, matchIndex) => (
                        <Box 
                          key={matchIndex} 
                          p={2} 
                          borderWidth="1px" 
                          borderRadius="md" 
                          bg="gray.50"
                        >
                          <Flex justify="space-between" mb={1}>
                            <Link 
                              color="blue.500" 
                              fontWeight="medium"
                              onClick={() => handleFileClick(fileMatch.file_path, match.line_number)}
                            >
                              Line {match.line_number}
                            </Link>
                          </Flex>
                          <Code p={2} borderRadius="md" fontSize="sm" whiteSpace="pre-wrap" display="block">
                            {highlightMatch(match.line, match.start, match.end)}
                          </Code>
                        </Box>
                      ))}
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </Box>
      )}
    </Box>
  );
};

export default RegexSearch;
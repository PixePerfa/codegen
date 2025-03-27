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
  Badge,
  Spinner,
  useToast,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Link,
  Code,
} from '@chakra-ui/react';
import { FiSearch, FiFile, FiCode } from 'react-icons/fi';
import { useApi } from '../services/api';

interface SymbolUsagesProps {
  projectId: string;
  onFileClick?: (filePath: string, line?: number) => void;
}

interface Usage {
  file_path: string;
  line: number;
  column: number;
  context?: string;
}

interface Symbol {
  name: string;
  type: string;
  file_path: string;
  line: number;
  column: number;
}

interface UsagesResponse {
  status: string;
  symbol: Symbol;
  usages: Usage[];
  message?: string;
}

const SymbolUsages: React.FC<SymbolUsagesProps> = ({ projectId, onFileClick }) => {
  const toast = useToast();
  const api = useApi();
  const [symbolName, setSymbolName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [usagesData, setUsagesData] = useState<UsagesResponse | null>(null);

  const handleSearch = async () => {
    if (!symbolName.trim()) {
      toast({
        title: 'Symbol name required',
        description: 'Please enter a symbol name to search for',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.get(`/projects/${projectId}/symbols/${encodeURIComponent(symbolName)}/usages`);
      if (response.status === 'success') {
        setUsagesData(response);
      } else {
        throw new Error(response.message || 'Failed to find symbol usages');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to find symbol usages',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      setUsagesData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileClick = (filePath: string, line?: number) => {
    if (onFileClick) {
      onFileClick(filePath, line);
    }
  };

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg" bg="white" shadow="sm">
      <Heading size="md" mb={4}>
        Find Symbol Usages
      </Heading>
      <Text mb={4}>
        Search for all usages of a symbol in the codebase.
      </Text>
      
      <Flex mb={6}>
        <Input
          placeholder="Enter symbol name (e.g., MyClass, my_function)"
          value={symbolName}
          onChange={(e) => setSymbolName(e.target.value)}
          mr={2}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        <Button
          leftIcon={<FiSearch />}
          colorScheme="blue"
          onClick={handleSearch}
          isLoading={isLoading}
          loadingText="Searching..."
        >
          Find Usages
        </Button>
      </Flex>

      {isLoading && (
        <Flex justify="center" my={8}>
          <Spinner size="xl" />
        </Flex>
      )}

      {!isLoading && usagesData && (
        <Box>
          <Box mb={4} p={3} borderWidth="1px" borderRadius="md" bg="gray.50">
            <Heading size="sm" mb={2}>Symbol Information</Heading>
            <HStack spacing={4}>
              <Badge colorScheme="blue">{usagesData.symbol.type}</Badge>
              <Text fontWeight="bold">{usagesData.symbol.name}</Text>
              <Text fontSize="sm">
                Defined in: 
                <Link 
                  color="blue.500" 
                  ml={1} 
                  onClick={() => handleFileClick(usagesData.symbol.file_path, usagesData.symbol.line)}
                >
                  {usagesData.symbol.file_path}:{usagesData.symbol.line}
                </Link>
              </Text>
            </HStack>
          </Box>

          <Heading size="sm" mb={3}>
            Usages ({usagesData.usages.length})
          </Heading>

          {usagesData.usages.length === 0 ? (
            <Text>No usages found.</Text>
          ) : (
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>File</Th>
                  <Th>Line</Th>
                  <Th>Context</Th>
                </Tr>
              </Thead>
              <Tbody>
                {usagesData.usages.map((usage, index) => (
                  <Tr key={index}>
                    <Td>
                      <Link 
                        color="blue.500" 
                        onClick={() => handleFileClick(usage.file_path, usage.line)}
                      >
                        <Flex align="center">
                          <FiFile style={{ marginRight: '8px' }} />
                          {usage.file_path}
                        </Flex>
                      </Link>
                    </Td>
                    <Td>{usage.line}:{usage.column}</Td>
                    <Td>
                      {usage.context ? (
                        <Code p={1} borderRadius="md" fontSize="xs" whiteSpace="pre-wrap">
                          {usage.context}
                        </Code>
                      ) : (
                        <Text fontSize="xs" color="gray.500">No context available</Text>
                      )}
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </Box>
      )}
    </Box>
  );
};

export default SymbolUsages;
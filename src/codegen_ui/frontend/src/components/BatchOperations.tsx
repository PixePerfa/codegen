import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Heading, 
  Spinner, 
  Text,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Button,
  Select,
  Checkbox,
  CheckboxGroup,
  Stack,
  VStack,
  HStack,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  CloseButton,
  Divider
} from '@chakra-ui/react';
import { fileApi, transformApi } from '../services/api';
import { File, BatchOperation, BatchResult } from '../types';

interface BatchOperationsProps {
  projectId: string;
  onOperationComplete?: () => void;
}

const BatchOperations: React.FC<BatchOperationsProps> = ({ projectId, onOperationComplete }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [operation, setOperation] = useState<string>('replace_text');
  const [pattern, setPattern] = useState<string>('');
  const [replacement, setReplacement] = useState<string>('');
  const [importStatement, setImportStatement] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(true);
  const [result, setResult] = useState<BatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    fetchFiles();
  }, [projectId]);

  const fetchFiles = async () => {
    try {
      setFilesLoading(true);
      const response = await fileApi.listFiles(projectId);
      // Only include source files
      const sourceFiles = response.data.filter((file: File) => file.is_source);
      setFiles(sourceFiles);
    } catch (error) {
      console.error('Error fetching files:', error);
      toast({
        title: 'Error fetching files',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setFilesLoading(false);
    }
  };

  const handleFileSelection = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value, checked } = e.target;
    if (checked) {
      setSelectedFiles(prev => [...prev, value]);
    } else {
      setSelectedFiles(prev => prev.filter(file => file !== value));
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedFiles(files.map(file => file.path));
    } else {
      setSelectedFiles([]);
    }
  };

  const handleSubmit = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    if (operation === 'replace_text' && (!pattern || !replacement)) {
      setError('Pattern and replacement are required for text replacement');
      return;
    }

    if ((operation === 'add_import' || operation === 'remove_import') && !importStatement) {
      setError('Import statement is required');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const batchOperation: BatchOperation = {
        operation,
        files: selectedFiles,
        params: operation === 'replace_text' 
          ? { pattern, replacement } 
          : { import_statement: importStatement }
      };

      const response = await transformApi.batchOperation(projectId, batchOperation);
      setResult(response.data);
      
      toast({
        title: 'Batch operation completed',
        description: `Operation applied to ${response.data.results.length} files`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      if (onOperationComplete) {
        onOperationComplete();
      }
    } catch (error) {
      console.error('Error performing batch operation:', error);
      setError('Error performing batch operation');
      toast({
        title: 'Error',
        description: 'Failed to perform batch operation',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (filesLoading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner />
        <Text mt={2}>Loading files...</Text>
      </Box>
    );
  }

  return (
    <Box h="100%" display="flex" flexDirection="column" p={4}>
      <Heading size="md" mb={4}>Batch Operations</Heading>
      
      {error && (
        <Alert status="error" mb={4}>
          <AlertIcon />
          <AlertTitle mr={2}>Error!</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
          <CloseButton 
            position="absolute" 
            right="8px" 
            top="8px" 
            onClick={() => setError(null)} 
          />
        </Alert>
      )}
      
      <FormControl mb={4}>
        <FormLabel>Operation Type</FormLabel>
        <Select 
          value={operation} 
          onChange={(e) => setOperation(e.target.value)}
        >
          <option value="replace_text">Replace Text</option>
          <option value="add_import">Add Import</option>
          <option value="remove_import">Remove Import</option>
        </Select>
      </FormControl>
      
      {operation === 'replace_text' ? (
        <>
          <FormControl mb={4}>
            <FormLabel>Pattern (Regex)</FormLabel>
            <Input 
              value={pattern} 
              onChange={(e) => setPattern(e.target.value)} 
              placeholder="Regular expression pattern"
            />
          </FormControl>
          
          <FormControl mb={4}>
            <FormLabel>Replacement</FormLabel>
            <Textarea 
              value={replacement} 
              onChange={(e) => setReplacement(e.target.value)} 
              placeholder="Replacement text"
              rows={3}
            />
          </FormControl>
        </>
      ) : (
        <FormControl mb={4}>
          <FormLabel>Import Statement</FormLabel>
          <Input 
            value={importStatement} 
            onChange={(e) => setImportStatement(e.target.value)} 
            placeholder={operation === 'add_import' ? "e.g., from module import name" : "Import to remove"}
          />
        </FormControl>
      )}
      
      <Divider my={4} />
      
      <FormControl mb={4}>
        <FormLabel>Select Files</FormLabel>
        <HStack mb={2}>
          <Checkbox onChange={handleSelectAll}>Select All</Checkbox>
          <Text ml="auto" fontSize="sm">
            {selectedFiles.length} of {files.length} files selected
          </Text>
        </HStack>
        
        <Box maxH="300px" overflowY="auto" borderWidth="1px" borderRadius="md" p={2}>
          <CheckboxGroup>
            <Stack spacing={1}>
              {files.map((file) => (
                <Checkbox 
                  key={file.path} 
                  value={file.path}
                  isChecked={selectedFiles.includes(file.path)}
                  onChange={handleFileSelection}
                >
                  <Text fontSize="sm" isTruncated maxW="500px" title={file.path}>
                    {file.path}
                  </Text>
                </Checkbox>
              ))}
            </Stack>
          </CheckboxGroup>
        </Box>
      </FormControl>
      
      <Button 
        colorScheme="brand" 
        onClick={handleSubmit} 
        isLoading={loading}
        isDisabled={selectedFiles.length === 0}
        alignSelf="flex-end"
      >
        Apply Operation
      </Button>
      
      {result && (
        <Box mt={4} borderWidth="1px" borderRadius="md" p={4}>
          <Heading size="sm" mb={2}>Operation Results</Heading>
          <VStack align="stretch" spacing={2} maxH="200px" overflowY="auto">
            {result.results.map((item, index) => (
              <Box key={index} p={2} bg="gray.50" _dark={{ bg: 'gray.700' }} borderRadius="md">
                <Text fontWeight="bold">{item.file}</Text>
                <Text fontSize="sm">{item.result}</Text>
              </Box>
            ))}
          </VStack>
        </Box>
      )}
    </Box>
  );
};

export default BatchOperations;
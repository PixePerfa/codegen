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
  Select,
  Textarea,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  useToast
} from '@chakra-ui/react';
import { FaMagic } from 'react-icons/fa';
import { transformApi } from '../services/api';

interface CodeTransformProps {
  projectId: string;
  onTransformComplete?: () => void;
}

const CodeTransform: React.FC<CodeTransformProps> = ({ projectId, onTransformComplete }) => {
  const [operation, setOperation] = useState('');
  const [params, setParams] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const operations = [
    { value: 'rename_symbol', label: 'Rename Symbol', params: ['symbol_name', 'new_name'] },
    { value: 'move_symbol', label: 'Move Symbol', params: ['symbol_name', 'target_file'] },
    { value: 'rename_file', label: 'Rename File', params: ['file_path', 'new_name'] },
    { value: 'commit', label: 'Commit Changes', params: [] },
    { value: 'git_commit', label: 'Git Commit', params: ['message'] },
  ];

  const handleOperationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedOperation = e.target.value;
    setOperation(selectedOperation);
    
    // Reset params when operation changes
    const selectedOpConfig = operations.find(op => op.value === selectedOperation);
    if (selectedOpConfig) {
      const newParams: Record<string, string> = {};
      selectedOpConfig.params.forEach(param => {
        newParams[param] = '';
      });
      setParams(newParams);
    }
    
    // Reset result and error
    setResult(null);
    setError(null);
  };

  const handleParamChange = (param: string, value: string) => {
    setParams(prev => ({
      ...prev,
      [param]: value
    }));
  };

  const handleTransform = async () => {
    // Validate required params
    const selectedOpConfig = operations.find(op => op.value === operation);
    if (!selectedOpConfig) return;
    
    const missingParams = selectedOpConfig.params.filter(param => !params[param]);
    if (missingParams.length > 0) {
      setError(`Missing required parameters: ${missingParams.join(', ')}`);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      
      const response = await transformApi.transform(projectId, {
        operation,
        params,
      });
      
      setResult(response.data.result);
      
      toast({
        title: 'Operation successful',
        description: `${selectedOpConfig.label} completed successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      if (onTransformComplete) {
        onTransformComplete();
      }
    } catch (error) {
      console.error('Error performing transformation:', error);
      setError(error instanceof Error ? error.message : 'Unknown error');
      
      toast({
        title: 'Error performing transformation',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box h="100%" display="flex" flexDirection="column">
      <VStack spacing={4} align="stretch">
        <FormControl isRequired>
          <FormLabel>Operation</FormLabel>
          <Select 
            placeholder="Select operation" 
            value={operation}
            onChange={handleOperationChange}
          >
            {operations.map(op => (
              <option key={op.value} value={op.value}>{op.label}</option>
            ))}
          </Select>
        </FormControl>
        
        {operation && operations.find(op => op.value === operation)?.params.map(param => (
          <FormControl key={param} isRequired>
            <FormLabel>{param.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</FormLabel>
            <Input 
              placeholder={`Enter ${param.replace(/_/g, ' ')}`} 
              value={params[param] || ''}
              onChange={(e) => handleParamChange(param, e.target.value)}
            />
          </FormControl>
        ))}
        
        {operation && (
          <Button 
            leftIcon={<FaMagic />} 
            colorScheme="brand" 
            onClick={handleTransform}
            isLoading={loading}
            isDisabled={!operation}
            mt={4}
          >
            Execute Transformation
          </Button>
        )}
        
        {loading && (
          <HStack justifyContent="center" py={4}>
            <Spinner />
            <Text>Executing transformation...</Text>
          </HStack>
        )}
        
        {error && (
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            <Box>
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Box>
          </Alert>
        )}
        
        {result && (
          <Alert status="success" borderRadius="md">
            <AlertIcon />
            <Box>
              <AlertTitle>Success</AlertTitle>
              <AlertDescription>
                <Text mb={2}>Transformation completed successfully.</Text>
                {result && (
                  <Box 
                    p={2} 
                    bg="gray.50" 
                    _dark={{ bg: 'gray.800' }}
                    borderRadius="md"
                    fontFamily="mono"
                    fontSize="sm"
                    whiteSpace="pre-wrap"
                  >
                    {result}
                  </Box>
                )}
              </AlertDescription>
            </Box>
          </Alert>
        )}
      </VStack>
    </Box>
  );
};

export default CodeTransform;
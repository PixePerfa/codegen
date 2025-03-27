import React, { useState } from 'react';
import { 
  Box, 
  Heading, 
  Spinner, 
  Text,
  FormControl,
  FormLabel,
  Input,
  Button,
  Select,
  VStack,
  HStack,
  useToast,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  CloseButton,
  Divider,
  Code,
  Badge
} from '@chakra-ui/react';
import { gitApi } from '../services/api';
import { GitOperation, GitResult } from '../types';

interface GitOperationsProps {
  projectId: string;
  onOperationComplete?: () => void;
}

const GitOperations: React.FC<GitOperationsProps> = ({ projectId, onOperationComplete }) => {
  const [operation, setOperation] = useState<string>('status');
  const [branchName, setBranchName] = useState<string>('');
  const [commitMessage, setCommitMessage] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GitResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const handleSubmit = async () => {
    if (operation === 'commit' && !commitMessage) {
      setError('Commit message is required');
      return;
    }

    if ((operation === 'checkout' || operation === 'create_branch') && !branchName) {
      setError('Branch name is required');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const gitOperation: GitOperation = {
        operation,
        params: operation === 'commit' 
          ? { message: commitMessage } 
          : operation === 'checkout' || operation === 'create_branch'
            ? { branch: branchName }
            : {}
      };

      const response = await gitApi.gitOperation(projectId, gitOperation);
      setResult(response.data);
      
      toast({
        title: 'Git operation completed',
        description: `Operation '${operation}' completed successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });

      if (onOperationComplete) {
        onOperationComplete();
      }
    } catch (error) {
      console.error('Error performing git operation:', error);
      setError('Error performing git operation');
      toast({
        title: 'Error',
        description: 'Failed to perform git operation',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const renderOperationForm = () => {
    switch (operation) {
      case 'commit':
        return (
          <FormControl mb={4}>
            <FormLabel>Commit Message</FormLabel>
            <Input 
              value={commitMessage} 
              onChange={(e) => setCommitMessage(e.target.value)} 
              placeholder="Enter commit message"
            />
          </FormControl>
        );
      case 'checkout':
      case 'create_branch':
        return (
          <FormControl mb={4}>
            <FormLabel>Branch Name</FormLabel>
            <Input 
              value={branchName} 
              onChange={(e) => setBranchName(e.target.value)} 
              placeholder="Enter branch name"
            />
          </FormControl>
        );
      default:
        return null;
    }
  };

  const formatGitResult = (result: any) => {
    if (typeof result === 'string') {
      return result;
    }
    
    if (Array.isArray(result)) {
      return result.join('\n');
    }
    
    return JSON.stringify(result, null, 2);
  };

  return (
    <Box h="100%" display="flex" flexDirection="column" p={4}>
      <Heading size="md" mb={4}>Git Operations</Heading>
      
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
          <option value="status">Status</option>
          <option value="commit">Commit</option>
          <option value="checkout">Checkout Branch</option>
          <option value="create_branch">Create Branch</option>
          <option value="pull">Pull</option>
          <option value="push">Push</option>
        </Select>
      </FormControl>
      
      {renderOperationForm()}
      
      <Button 
        colorScheme="brand" 
        onClick={handleSubmit} 
        isLoading={loading}
        mb={4}
      >
        Execute Git Operation
      </Button>
      
      {loading && (
        <Box textAlign="center" py={4}>
          <Spinner />
          <Text mt={2}>Executing git operation...</Text>
        </Box>
      )}
      
      {result && (
        <Box mt={4} borderWidth="1px" borderRadius="md" p={4} overflowX="auto">
          <HStack mb={2}>
            <Heading size="sm">Operation Result</Heading>
            <Badge colorScheme="green" ml={2}>{operation}</Badge>
          </HStack>
          <Divider mb={3} />
          <Code display="block" whiteSpace="pre" p={3} borderRadius="md" overflowX="auto">
            {formatGitResult(result.result)}
          </Code>
        </Box>
      )}
    </Box>
  );
};

export default GitOperations;
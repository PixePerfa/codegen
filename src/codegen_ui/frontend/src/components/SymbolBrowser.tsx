import React, { useState, useEffect } from 'react';
import { 
  Box, 
  VStack, 
  HStack, 
  Text, 
  Icon, 
  Spinner,
  Input,
  InputGroup,
  InputLeftElement,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  useColorModeValue,
  useToast
} from '@chakra-ui/react';
import { FaSearch, FaCode, FaCube, FaFunction } from 'react-icons/fa';
import { symbolApi, fileApi } from '../services/api';
import { Symbol, Class, Function, File } from '../types';

interface SymbolBrowserProps {
  projectId: string;
  onSymbolSelect: (file: File) => void;
}

const SymbolBrowser: React.FC<SymbolBrowserProps> = ({ projectId, onSymbolSelect }) => {
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [classes, setClasses] = useState<Class[]>([]);
  const [functions, setFunctions] = useState<Function[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const toast = useToast();
  
  const bgHover = useColorModeValue('gray.100', 'gray.700');

  useEffect(() => {
    fetchSymbols();
  }, [projectId]);

  const fetchSymbols = async () => {
    try {
      setLoading(true);
      
      // Fetch all symbols in parallel
      const [symbolsResponse, classesResponse, functionsResponse] = await Promise.all([
        symbolApi.listSymbols(projectId),
        symbolApi.listClasses(projectId),
        symbolApi.listFunctions(projectId),
      ]);
      
      setSymbols(symbolsResponse.data);
      setClasses(classesResponse.data);
      setFunctions(functionsResponse.data);
    } catch (error) {
      console.error('Error fetching symbols:', error);
      toast({
        title: 'Error fetching symbols',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolClick = async (symbol: Symbol) => {
    if (!symbol.file_path) return;
    
    try {
      const response = await fileApi.getFile(projectId, symbol.file_path);
      onSymbolSelect(response.data);
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

  const filterSymbols = (items: Symbol[]) => {
    if (!searchQuery) return items;
    
    return items.filter(item => 
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.file_path && item.file_path.toLowerCase().includes(searchQuery.toLowerCase()))
    );
  };

  const renderSymbolList = (items: Symbol[], icon: React.ReactElement) => {
    const filteredItems = filterSymbols(items);
    
    return (
      <VStack align="stretch" spacing={0}>
        {filteredItems.length === 0 ? (
          <Text p={4} textAlign="center">No symbols found</Text>
        ) : (
          filteredItems.map((item, index) => (
            <HStack
              key={`${item.name}-${index}`}
              py={2}
              px={4}
              cursor="pointer"
              _hover={{ bg: bgHover }}
              onClick={() => handleSymbolClick(item)}
            >
              {React.cloneElement(icon, { color: 'blue.500' })}
              <Box>
                <Text fontWeight="medium">{item.name}</Text>
                {item.file_path && (
                  <Text fontSize="sm" color="gray.500">{item.file_path}</Text>
                )}
              </Box>
              <Badge ml="auto">{item.type}</Badge>
            </HStack>
          ))
        )}
      </VStack>
    );
  };

  const renderClassList = () => {
    const filteredClasses = filterSymbols(classes);
    
    return (
      <VStack align="stretch" spacing={0}>
        {filteredClasses.length === 0 ? (
          <Text p={4} textAlign="center">No classes found</Text>
        ) : (
          filteredClasses.map((cls, index) => (
            <Box key={`${cls.name}-${index}`}>
              <HStack
                py={2}
                px={4}
                cursor="pointer"
                _hover={{ bg: bgHover }}
                onClick={() => handleSymbolClick(cls)}
              >
                <Icon as={FaCube} color="purple.500" />
                <Box>
                  <Text fontWeight="medium">{cls.name}</Text>
                  {cls.file_path && (
                    <Text fontSize="sm" color="gray.500">{cls.file_path}</Text>
                  )}
                </Box>
                <Badge ml="auto">Class</Badge>
              </HStack>
              
              {cls.methods.length > 0 && (
                <VStack align="stretch" spacing={0} pl={8}>
                  {cls.methods.map((method, methodIndex) => (
                    <HStack
                      key={`${cls.name}-${method.name}-${methodIndex}`}
                      py={1}
                      px={4}
                      cursor="pointer"
                      _hover={{ bg: bgHover }}
                      onClick={() => handleSymbolClick({
                        ...cls,
                        name: method.name,
                        line: method.line,
                        column: method.column
                      })}
                    >
                      <Icon as={FaFunction} color="green.500" />
                      <Text>{method.name}</Text>
                      <Badge ml="auto" colorScheme="green">Method</Badge>
                    </HStack>
                  ))}
                </VStack>
              )}
            </Box>
          ))
        )}
      </VStack>
    );
  };

  const renderFunctionList = () => {
    const filteredFunctions = filterSymbols(functions);
    
    return (
      <VStack align="stretch" spacing={0}>
        {filteredFunctions.length === 0 ? (
          <Text p={4} textAlign="center">No functions found</Text>
        ) : (
          filteredFunctions.map((func, index) => (
            <HStack
              key={`${func.name}-${index}`}
              py={2}
              px={4}
              cursor="pointer"
              _hover={{ bg: bgHover }}
              onClick={() => handleSymbolClick(func)}
            >
              <Icon as={FaFunction} color="green.500" />
              <Box>
                <Text fontWeight="medium">{func.name}</Text>
                {func.file_path && (
                  <Text fontSize="sm" color="gray.500">{func.file_path}</Text>
                )}
                {func.parameters.length > 0 && (
                  <Text fontSize="xs" color="gray.500">
                    Parameters: {func.parameters.join(', ')}
                  </Text>
                )}
              </Box>
              <Badge ml="auto">Function</Badge>
            </HStack>
          ))
        )}
      </VStack>
    );
  };

  return (
    <Box h="100%" display="flex" flexDirection="column">
      <InputGroup mb={4}>
        <InputLeftElement pointerEvents="none">
          <Icon as={FaSearch} color="gray.500" />
        </InputLeftElement>
        <Input 
          placeholder="Search symbols..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </InputGroup>
      
      {loading ? (
        <Box textAlign="center" py={8}>
          <Spinner />
          <Text mt={2}>Loading symbols...</Text>
        </Box>
      ) : (
        <Tabs isFitted variant="enclosed" flex="1" display="flex" flexDirection="column">
          <TabList>
            <Tab>All</Tab>
            <Tab>Classes</Tab>
            <Tab>Functions</Tab>
          </TabList>
          
          <TabPanels flex="1" overflowY="auto">
            <TabPanel p={0}>
              {renderSymbolList(symbols, <Icon as={FaCode} />)}
            </TabPanel>
            <TabPanel p={0}>
              {renderClassList()}
            </TabPanel>
            <TabPanel p={0}>
              {renderFunctionList()}
            </TabPanel>
          </TabPanels>
        </Tabs>
      )}
    </Box>
  );
};

export default SymbolBrowser;
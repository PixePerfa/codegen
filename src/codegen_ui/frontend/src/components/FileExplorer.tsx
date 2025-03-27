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
  useColorModeValue,
  useToast
} from '@chakra-ui/react';
import { FaFolder, FaFolderOpen, FaFile, FaSearch, FaCode } from 'react-icons/fa';
import { fileApi } from '../services/api';
import { File } from '../types';

interface FileExplorerProps {
  projectId: string;
  onFileSelect: (file: File) => void;
}

interface FileNode {
  path: string;
  name: string;
  isDirectory: boolean;
  children: FileNode[];
  isSource: boolean;
}

const FileExplorer: React.FC<FileExplorerProps> = ({ projectId, onFileSelect }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const toast = useToast();
  
  const bgHover = useColorModeValue('gray.100', 'gray.700');

  useEffect(() => {
    fetchFiles();
  }, [projectId]);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await fileApi.listFiles(projectId);
      setFiles(response.data);
      buildFileTree(response.data);
    } catch (error) {
      console.error('Error fetching files:', error);
      toast({
        title: 'Error fetching files',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const buildFileTree = (files: File[]) => {
    const root: FileNode = {
      path: '',
      name: 'root',
      isDirectory: true,
      children: [],
      isSource: false,
    };

    // Sort files to ensure directories come first
    const sortedFiles = [...files].sort((a, b) => {
      const pathA = a.path.split('/');
      const pathB = b.path.split('/');
      return pathA.length - pathB.length;
    });

    for (const file of sortedFiles) {
      const pathParts = file.path.split('/');
      let currentNode = root;

      // Create path hierarchy
      for (let i = 0; i < pathParts.length; i++) {
        const part = pathParts[i];
        const isLastPart = i === pathParts.length - 1;
        const currentPath = pathParts.slice(0, i + 1).join('/');
        
        // Find existing node or create new one
        let foundNode = currentNode.children.find(child => child.name === part);
        
        if (!foundNode) {
          const newNode: FileNode = {
            path: currentPath,
            name: part,
            isDirectory: !isLastPart,
            children: [],
            isSource: isLastPart ? file.is_source : false,
          };
          
          currentNode.children.push(newNode);
          foundNode = newNode;
        }
        
        currentNode = foundNode;
      }
    }

    // Sort children alphabetically with directories first
    const sortNodes = (node: FileNode) => {
      node.children.sort((a, b) => {
        if (a.isDirectory && !b.isDirectory) return -1;
        if (!a.isDirectory && b.isDirectory) return 1;
        return a.name.localeCompare(b.name);
      });
      
      for (const child of node.children) {
        if (child.isDirectory) {
          sortNodes(child);
        }
      }
    };
    
    sortNodes(root);
    setFileTree(root);
  };

  const toggleFolder = (path: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  const handleFileClick = async (file: FileNode) => {
    try {
      const response = await fileApi.getFile(projectId, file.path);
      onFileSelect(response.data);
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

  const renderFileTree = (node: FileNode, level = 0) => {
    // Skip rendering the root node itself
    if (level === 0) {
      return node.children.map(child => renderFileTree(child, level + 1));
    }

    // Filter by search query if one exists
    if (searchQuery && !node.path.toLowerCase().includes(searchQuery.toLowerCase())) {
      // If this is a directory, check if any children match
      if (node.isDirectory) {
        const matchingChildren = node.children.filter(child => 
          child.path.toLowerCase().includes(searchQuery.toLowerCase())
        );
        if (matchingChildren.length === 0) {
          return null;
        }
      } else {
        return null;
      }
    }

    const isExpanded = expandedFolders.has(node.path);
    const paddingLeft = level * 16;

    return (
      <Box key={node.path}>
        <HStack 
          py={1} 
          px={2} 
          cursor="pointer" 
          _hover={{ bg: bgHover }}
          onClick={() => node.isDirectory ? toggleFolder(node.path) : handleFileClick(node)}
          pl={`${paddingLeft}px`}
        >
          <Icon 
            as={
              node.isDirectory 
                ? (isExpanded ? FaFolderOpen : FaFolder) 
                : (node.isSource ? FaCode : FaFile)
            } 
            color={
              node.isDirectory 
                ? "yellow.500" 
                : (node.isSource ? "blue.500" : "gray.500")
            }
          />
          <Text>{node.name}</Text>
        </HStack>
        
        {node.isDirectory && isExpanded && (
          <VStack align="stretch" spacing={0}>
            {node.children.map(child => renderFileTree(child, level + 1))}
          </VStack>
        )}
      </Box>
    );
  };

  return (
    <Box h="100%" overflowY="auto">
      <InputGroup mb={4}>
        <InputLeftElement pointerEvents="none">
          <Icon as={FaSearch} color="gray.500" />
        </InputLeftElement>
        <Input 
          placeholder="Search files..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </InputGroup>
      
      {loading ? (
        <Box textAlign="center" py={8}>
          <Spinner />
          <Text mt={2}>Loading files...</Text>
        </Box>
      ) : fileTree ? (
        <VStack align="stretch" spacing={0}>
          {renderFileTree(fileTree)}
        </VStack>
      ) : (
        <Text>No files found</Text>
      )}
    </Box>
  );
};

export default FileExplorer;
import React, { useRef, useEffect, useState } from 'react';
import { Box, Button, HStack, useToast } from '@chakra-ui/react';
import Editor, { Monaco } from '@monaco-editor/react';
import { File } from '../types';
import { fileApi } from '../services/api';

interface CodeEditorProps {
  file: File | null;
  projectId: string;
  onSave?: () => void;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ file, projectId, onSave }) => {
  const [content, setContent] = useState<string>('');
  const [language, setLanguage] = useState<string>('plaintext');
  const [isDirty, setIsDirty] = useState(false);
  const editorRef = useRef<any>(null);
  const toast = useToast();

  useEffect(() => {
    if (file) {
      setContent(file.content || '');
      setLanguage(getLanguageFromFilename(file.path));
      setIsDirty(false);
    }
  }, [file]);

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    
    // Set up editor options
    editor.updateOptions({
      fontSize: 14,
      fontFamily: '"Fira Code", Menlo, Monaco, "Courier New", monospace',
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      automaticLayout: true,
    });
  };

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined && value !== content) {
      setContent(value);
      setIsDirty(true);
    }
  };

  const handleSave = async () => {
    if (!file || !isDirty) return;

    try {
      await fileApi.updateFile(projectId, file.path, {
        path: file.path,
        content,
      });
      
      setIsDirty(false);
      
      toast({
        title: 'File saved',
        description: `${file.path} saved successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      if (onSave) {
        onSave();
      }
    } catch (error) {
      console.error('Error saving file:', error);
      toast({
        title: 'Error saving file',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const getLanguageFromFilename = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    
    const languageMap: Record<string, string> = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'sh': 'shell',
      'bash': 'shell',
      'c': 'c',
      'cpp': 'cpp',
      'h': 'cpp',
      'java': 'java',
      'go': 'go',
      'rs': 'rust',
      'php': 'php',
      'rb': 'ruby',
      'sql': 'sql',
    };
    
    return extension ? (languageMap[extension] || 'plaintext') : 'plaintext';
  };

  return (
    <Box h="100%" display="flex" flexDirection="column">
      <HStack justifyContent="flex-end" p={2} bg="gray.100" _dark={{ bg: 'gray.700' }}>
        <Button 
          size="sm" 
          colorScheme="brand" 
          onClick={handleSave}
          isDisabled={!file || !isDirty}
        >
          Save
        </Button>
      </HStack>
      <Box flex="1">
        <Editor
          height="100%"
          language={language}
          value={content}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            readOnly: !file,
          }}
        />
      </Box>
    </Box>
  );
};

export default CodeEditor;
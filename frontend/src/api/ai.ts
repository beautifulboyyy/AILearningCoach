export async function chatStream(
  message: string, 
  onMessage: (content: string) => void,
  onReferences: (refs: any[]) => void
) {
  const response = await fetch('http://localhost:8000/api/v1/ai/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) return;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const dataStr = line.slice(6);
        if (dataStr === '[DONE]') break;
        
        try {
          const data = JSON.parse(dataStr);
          if (data.type === 'content') {
            onMessage(data.data);
          } else if (data.type === 'references') {
            onReferences(data.data);
          }
        } catch (e) {
          console.error('Error parsing SSE data', e);
        }
      }
    }
  }
}

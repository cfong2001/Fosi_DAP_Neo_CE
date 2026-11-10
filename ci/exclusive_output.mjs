import {open} from 'node:fs/promises';

// The exclusive create rejects existing files, hard links and symbolic links,
// including dangling symlinks. Never truncate a pre-existing path.
export async function writeNewOutput(path, bytes) {
  const file = await open(path, 'wx');
  try {
    await file.writeFile(bytes);
  } finally {
    await file.close();
  }
}

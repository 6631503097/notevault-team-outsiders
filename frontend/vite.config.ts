import { defineConfig } from 'vitest/config';
export default defineConfig({server:{proxy:{'/api':{target:'http://127.0.0.1:8081'}}},test:{environment:'jsdom',globals:true,setupFiles:'./src/test-setup.ts'}});

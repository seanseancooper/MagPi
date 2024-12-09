//import { defineConfig } from 'vite'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

export default {
    root: '../src',
    plugins: [
        nodePolyfills(),
    ],
    build: {
        outDir: '../static',
        emptyOutDir: true, // necessary
    },
}

//export default defineConfig({
//  plugins: [
//    nodePolyfills(),
//  ],
//})


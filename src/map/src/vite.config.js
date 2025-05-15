//import { defineConfig } from 'vite'
import { nodePolyfills } from 'vite-plugin-node-polyfills'
import map_config from '../../config/map.json' assert { type: 'json' };

// read config
const map_host = map_config.MAP.find(item => item.MAP_HOST)['MAP_HOST'];
const map_port = map_config.MAP.find(item => item.MAP_PORT)['MAP_PORT'];

export default {
    root: '../src',
    plugins: [
        nodePolyfills(),
    ],
    build: {
        outDir: '../static',
        emptyOutDir: true, // necessary
    },
    server: {
        host: map_host,
        port: map_port,
    },
}

//export default defineConfig({
//  plugins: [
//    nodePolyfills(),
//  ],
//})


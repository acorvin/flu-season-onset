import '@fontsource-variable/geist';
import '@fontsource-variable/geist-mono';
import { mount } from 'svelte';
import FluRings from './lib/FluRings.svelte';

document.body.style.margin = '0';
document.body.style.padding = '24px 16px';
document.body.style.background = '#fff';
mount(FluRings, { target: document.getElementById('app'), props: { title: true } });

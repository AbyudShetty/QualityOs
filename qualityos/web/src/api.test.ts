import {describe,it,expect} from 'vitest';
import {pretty,date,canWrite,qaRequired} from './api';
describe('operator presentation boundaries',()=>{
 it('preserves QA as a separate signing role',()=>{expect(qaRequired('authorize')).toBe(true);expect(qaRequired('produce')).toBe(false);expect(canWrite({id:'v',username:'v',display_name:'Viewer',role:'VIEWER'})).toBe(false)});
 it('does not give administrators QA writing by default',()=>{expect(canWrite({id:'a',username:'a',display_name:'Admin',role:'ADMIN'})).toBe(false)});
 it('renders explicit UTC and readable states',()=>{expect(date('2026-01-15T08:00:00Z')).toContain('UTC');expect(pretty('CURRENT_REASSESSMENT')).toBe('Current reassessment')});
});

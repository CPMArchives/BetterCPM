/* Read-only host observer for the bounded BetterCP/M cpmsim qualification.
 * Included in simz80.c, not in guest code. No instruction semantics change.
 * Each configured owner has low/top offsets and optionally a live base pointer.
 * Actual LD SP instructions select an owner; subsequent PUSH/CALL/POP effects
 * stay with that owner even when they cross its bounds. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { char name[32]; unsigned low,top,ptr,max,resume; } bc_band;
typedef struct { unsigned pc,op,sub,before,after,next; } bc_step;
static bc_band bc_bands[24];
static bc_step bc_ring[64], bc_pending;
static unsigned bc_n,bc_idx,bc_lo,bc_top;
static int bc_init,bc_owner=-1;
static FILE *bc_log;
static unsigned bc_commit_start,bc_commit_end,bc_commit_signature[16];
static int bc_commit_enabled,bc_commit_active;
static unsigned bc_word(unsigned addr) {
    return getmem(addr) | ((unsigned)getmem((addr+1)&65535)<<8);
}
static void bc_before(void) {
    if (!bc_init) {
        bc_init=1;
        const char *cfg=getenv("BCPM_STACK_CONFIG"),*log=getenv("BCPM_STACK_TRACE");
        if (cfg && log) {
            FILE *f=fopen(cfg,"r"); bc_log=fopen(log,"w");
            if (!f || !bc_log) { perror("stack trace setup"); exit(85); }
            while (bc_n<24 && fscanf(f,"%31s %x %x %x",bc_bands[bc_n].name,
                    &bc_bands[bc_n].low,&bc_bands[bc_n].top,&bc_bands[bc_n].ptr)==4) {
                fprintf(bc_log,"BAND %s %04x %04x %04x\n",bc_bands[bc_n].name,
                        bc_bands[bc_n].low,bc_bands[bc_n].top,bc_bands[bc_n].ptr);
                bc_n++;
            }
            fclose(f); fflush(bc_log);
            const char *commit=getenv("BCPM_COMMIT_CONFIG");
            if (commit) {
                f=fopen(commit,"r");
                if (!f || fscanf(f,"%x %x",&bc_commit_start,&bc_commit_end)!=2) exit(85);
                for (unsigned i=0;i<16;i++) if(fscanf(f,"%x",&bc_commit_signature[i])!=1) exit(85);
                fclose(f);bc_commit_enabled=1;
            }
        }
    }
    if (!bc_log) return;
    if (bc_commit_enabled && !bc_commit_active && PC==bc_commit_start) {
        int match=1;
        for(unsigned i=0;i<16;i++) if(getmem((PC+i)&65535)!=bc_commit_signature[i]) match=0;
        if(match) {bc_commit_active=1;fprintf(bc_log,"COMMIT_BEGIN %04x\n",PC);fflush(bc_log);}
    }
    if (bc_commit_active && PC==bc_commit_end) {
        bc_commit_active=0;fprintf(bc_log,"COMMIT_END %04x\n",PC);fflush(bc_log);
    }
    bc_pending=(bc_step){PC,getmem(PC),getmem((PC+1)&65535),SP,0,0};
    if (bc_commit_active && ((bc_pending.op==0xd3 && bc_pending.sub==13) ||
            (bc_pending.op==0xed && bc_pending.sub==0x79 && C==13))) {
        fprintf(bc_log,"DISK_IO_DURING_COMMIT %04x\n",PC);fflush(bc_log);exit(87);
    }
}
static void bc_after(void) {
    if (!bc_log) return;
    bc_pending.after=SP; bc_pending.next=PC;
    if (bc_pending.before!=SP) bc_ring[bc_idx++%64]=bc_pending;
    unsigned op=bc_pending.op, sub=bc_pending.sub;
    if (op==0x31 || op==0xf9 || (op==0xed && sub==0x7b) ||
            ((op==0xdd || op==0xfd) && sub==0xf9)) {
        if (bc_owner>=0) bc_bands[bc_owner].resume=bc_pending.before;
        bc_owner=-1;
        for (unsigned i=0;i<bc_n;i++) {
            unsigned base=bc_bands[i].ptr ? bc_word(bc_bands[i].ptr):0;
            if (bc_bands[i].ptr && !base) continue;
            unsigned low=base+bc_bands[i].low,top=base+bc_bands[i].top;
            int entry=(SP==top || (bc_bands[i].resume && SP==bc_bands[i].resume) ||
                       (!strcmp(bc_bands[i].name,"manager") && SP==top-6));
            if (entry && low<=SP && SP<=top && top<=65536) {
                bc_owner=(int)i;bc_lo=low;bc_top=top;break;
            }
        }
    }
    if (bc_owner<0) return;
    bc_band *b=&bc_bands[bc_owner];
    if (SP>bc_top) {bc_owner=-1;return;}
    unsigned used=bc_top-SP;
    if (used>b->max || SP<bc_lo) {
        b->max=used;
        fprintf(bc_log,"MIN %s %u %04x %04x %04x %04x\n",b->name,used,bc_lo,bc_top,SP,bc_pending.pc);
        unsigned begin=bc_idx>64?bc_idx-64:0;
        for (unsigned j=begin;j<bc_idx;j++) {
            bc_step *s=&bc_ring[j%64];
            fprintf(bc_log,"  %04x %02x%02x %04x>%04x ->%04x\n",s->pc,s->op,s->sub,s->before,s->after,s->next);
        }
        fflush(bc_log);
    }
    if (SP<bc_lo) {fprintf(bc_log,"OVERFLOW %s\n",b->name);fflush(bc_log);exit(86);}
}

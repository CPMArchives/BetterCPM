/* Serial-only Cromemco test configuration. Video cards are absent.
 * Any video access fails explicitly rather than masquerading as tested video. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int slf;
uint8_t bg_color[3], fg_color[3];
static void unsupported(void) {
    fputs("Unconfigured Cromemco video or auxiliary card accessed\n", stderr);
    exit(1);
}
void proctec_vdm_off(void) {}
void cromemco_dazzler_off(void) {}
void proctec_vdm_ctl_out(unsigned char data) { (void)data; unsupported(); }
unsigned char proctec_vdm_kbd_status_in(void) { unsupported(); return 0xff; }
unsigned char proctec_vdm_kbd_in(void) { unsupported(); return 0xff; }
void cromemco_dazzler_ctl_out(unsigned char data) { (void)data; unsupported(); }
void cromemco_dazzler_format_out(unsigned char data) { (void)data; unsupported(); }
unsigned char cromemco_dazzler_flags_in(void) { unsupported(); return 0xff; }
unsigned char bettercpm_absent_in(void) { unsupported(); return 0xff; }
void bettercpm_absent_out(unsigned char data) { (void)data; unsupported(); }

#ifndef CBG_ETHORNELL_H
#define CBG_ETHORNELL_H

#include <stdint.h>

/**
 * check if "data" is a "CompressedBG___" file
 */
int cbg_is_valid(uint8_t * data, uint32_t size);

/**
 * decrypt the file.
 * WARNING: you have to check yourself if "crypted" is a valid file with "cbg_is_valid"
 *          before calling "cbg_decrypt"
 */
uint8_t * cbg_decrypt(uint8_t * crypted, uint32_t * pSize, uint32_t * pWidth, uint32_t * pHeight, uint32_t * pBitDepth);

void cbg_free(uint8_t * decrypted);

/**
 * save the file in PNG format (and append ".png" to "filename").
 */
// int cbg_save(uint8_t * data, uint32_t width, uint32_t height, const char * filename);

#endif


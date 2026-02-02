#!/usr/bin/env python3
"""
A straightforward image manipulation tool for basic pixel-level transformations.
Supports math operations (XOR, addition, subtraction) and channel swapping.
All operations are reversible.
"""

import argparse
import os
import sys
from PIL import Image


class ImageCipher:
    """Handles reversible pixel-level image transformations."""
    
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self._validate_input()
        
    def _validate_input(self):
        """Make sure the input file actually exists."""
        if not os.path.isfile(self.input_file):
            raise FileNotFoundError(f"Can't find image: {self.input_file}")
    
    def _validate_key(self, key):
        """Check that key is in valid range."""
        if key is None:
            raise ValueError("Need a key value (0-255) for this operation")
        if not isinstance(key, int) or key < 0 or key > 255:
            raise ValueError("Key needs to be an integer from 0 to 255")
        return key
    
    def _extract_channels(self, pixel):
        """Pull out RGBA values from a pixel, adding alpha if needed."""
        if len(pixel) == 3:
            r, g, b = pixel
            a = 255
        else:
            r, g, b, a = pixel
        return r, g, b, a
    
    def _apply_channel_math(self, pixel, operation, key):
        """Apply mathematical operation to RGB channels."""
        r, g, b, a = self._extract_channels(pixel)
        
        if operation == "xor":
            r, g, b = r ^ key, g ^ key, b ^ key
        elif operation == "add":
            r = (r + key) % 256
            g = (g + key) % 256
            b = (b + key) % 256
        elif operation == "sub":
            r = (r - key) % 256
            g = (g - key) % 256
            b = (b - key) % 256
        
        return (r, g, b, a)
    
    def _swap_channels(self, pixel, swap_type):
        """Swap two color channels."""
        r, g, b, a = self._extract_channels(pixel)
        
        swaps = {
            "rg": (g, r, b, a),
            "rb": (b, g, r, a),
            "gb": (r, b, g, a)
        }
        
        if swap_type not in swaps:
            raise ValueError(f"Invalid swap type: {swap_type}")
            
        return swaps[swap_type]
    
    def transform(self, mode, operation, key=None, swap_type=None):
        """
        Main transformation method.
        
        Args:
            mode: 'encrypt' or 'decrypt'
            operation: 'xor', 'add', 'sub', or 'swap'
            key: numeric key for math operations
            swap_type: which channels to swap ('rg', 'rb', 'gb')
        """
        img = Image.open(self.input_file).convert("RGBA")
        width, height = img.size
        pixels = list(img.getdata())
        transformed = []
        
        # Handle math-based operations
        if operation in ["xor", "add", "sub"]:
            validated_key = self._validate_key(key)
            
            # Figure out the actual operation to perform
            actual_op = operation
            if mode == "decrypt":
                # Reverse the operation for decryption
                if operation == "add":
                    actual_op = "sub"
                elif operation == "sub":
                    actual_op = "add"
                # XOR reverses itself
            
            for pixel in pixels:
                new_pixel = self._apply_channel_math(pixel, actual_op, validated_key)
                transformed.append(new_pixel)
        
        # Handle channel swapping
        elif operation == "swap":
            if not swap_type or swap_type not in ["rg", "rb", "gb"]:
                raise ValueError("Need to specify swap type: rg, rb, or gb")
            
            # Swaps are their own inverse, so same operation for encrypt/decrypt
            for pixel in pixels:
                new_pixel = self._swap_channels(pixel, swap_type)
                transformed.append(new_pixel)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Create the output image
        output_img = Image.new("RGBA", (width, height))
        output_img.putdata(transformed)
        
        # Save in appropriate format
        self._save_output(output_img)
        return self.output_file
    
    def _save_output(self, img):
        """Save image, handling format conversions as needed."""
        _, ext = os.path.splitext(self.output_file)
        
        # JPEG doesn't support transparency
        if ext.lower() in [".jpg", ".jpeg"]:
            img = img.convert("RGB")
        
        img.save(self.output_file)


def setup_parser():
    """Configure command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Transform images using reversible pixel operations"
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input image path"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output image path"
    )
    parser.add_argument(
        "-m", "--mode",
        required=True,
        choices=["encrypt", "decrypt"],
        help="Whether to encrypt or decrypt"
    )
    parser.add_argument(
        "--op",
        required=True,
        choices=["xor", "add", "sub", "swap"],
        help="Type of transformation (xor/add/sub/swap)"
    )
    parser.add_argument(
        "-k", "--key",
        type=int,
        help="Numeric key for math operations (0-255)"
    )
    parser.add_argument(
        "-s", "--swap",
        choices=["rg", "rb", "gb"],
        help="Channel swap configuration (for swap operation)"
    )
    
    return parser


def run():
    """Main entry point."""
    parser = setup_parser()
    args = parser.parse_args()
    
    try:
        cipher = ImageCipher(args.input, args.output)
        result = cipher.transform(
            mode=args.mode,
            operation=args.op,
            key=args.key,
            swap_type=args.swap
        )
        print(f"✓ Successfully wrote {result}")
        
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run()
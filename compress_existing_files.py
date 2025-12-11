"""
Compress existing files in the database
This script will update all existing files to use compression

WARNING: Make a backup of your database before running this!
"""

from app import create_app
from app.extensions import db
from app.models import File, HDRI, GalleryFile
from app.compression_utils import compress_file, decompress_file, get_compression_ratio, format_size
import sys

def compress_existing_files():
    """Compress all existing files in the database"""
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("DATABASE FILE COMPRESSION UTILITY")
        print("="*60)
        print("\n⚠️  WARNING: Make sure you have a backup of your database!")
        print("This will compress all existing files in the database.\n")
        
        response = input("Do you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
        
        print("\nStarting compression process...\n")
        
        # Compress Files table
        print("📁 Compressing Files...")
        files = File.query.all()
        total_original_size = 0
        total_compressed_size = 0
        files_compressed = 0
        
        for file in files:
            file_size = 0
            compressed_size = 0
            
            try:
                # Try to decompress - if it works, already compressed
                if file.banner_path:
                    try:
                        decompress_file(file.banner_path)
                        print(f"  ℹ️  {file.file_name} - Banner already compressed")
                    except:
                        # Not compressed, compress it
                        original = len(file.banner_path)
                        file.banner_path = compress_file(file.banner_path)
                        compressed = len(file.banner_path)
                        file_size += original
                        compressed_size += compressed
                        print(f"  ✓ {file.file_name} - Banner: {format_size(original)} → {format_size(compressed)}")
                
                # Compress GLB file
                if file.file_path_glb:
                    try:
                        decompress_file(file.file_path_glb)
                        print(f"  ℹ️  {file.file_name} - GLB already compressed")
                    except:
                        original = len(file.file_path_glb)
                        file.file_path_glb = compress_file(file.file_path_glb)
                        compressed = len(file.file_path_glb)
                        file_size += original
                        compressed_size += compressed
                        print(f"  ✓ {file.file_name} - GLB: {format_size(original)} → {format_size(compressed)}")
                
                # Compress ZIP file
                if file.file_path_zip:
                    try:
                        decompress_file(file.file_path_zip)
                        print(f"  ℹ️  {file.file_name} - ZIP already compressed")
                    except:
                        original = len(file.file_path_zip)
                        file.file_path_zip = compress_file(file.file_path_zip)
                        compressed = len(file.file_path_zip)
                        file_size += original
                        compressed_size += compressed
                        print(f"  ✓ {file.file_name} - ZIP: {format_size(original)} → {format_size(compressed)}")
                
                total_original_size += file_size
                total_compressed_size += compressed_size
                if file_size > 0:
                    files_compressed += 1
                    
            except Exception as e:
                print(f"  ❌ Error compressing {file.file_name}: {str(e)}")
        
        db.session.commit()
        print(f"\n✅ Compressed {files_compressed} files")
        
        # Compress Gallery Files
        print("\n🖼️  Compressing Gallery Images...")
        gallery_files = GalleryFile.query.all()
        gallery_compressed = 0
        
        for gf in gallery_files:
            try:
                # Check if already compressed
                try:
                    decompress_file(gf.file_path)
                    print(f"  ℹ️  Gallery #{gf.id} already compressed")
                    continue
                except:
                    pass
                
                original = len(gf.file_path)
                gf.file_path = compress_file(gf.file_path)
                compressed = len(gf.file_path)
                total_original_size += original
                total_compressed_size += compressed
                gallery_compressed += 1
                print(f"  ✓ Gallery #{gf.id}: {format_size(original)} → {format_size(compressed)}")
                
            except Exception as e:
                print(f"  ❌ Error compressing gallery #{gf.id}: {str(e)}")
        
        db.session.commit()
        print(f"\n✅ Compressed {gallery_compressed} gallery images")
        
        # Compress HDRI Files
        print("\n🌅 Compressing HDRIs...")
        hdris = HDRI.query.all()
        hdri_compressed = 0
        
        for hdri in hdris:
            hdri_size = 0
            hdri_comp = 0
            
            try:
                # Compress HDRI file
                if hdri.file_path:
                    try:
                        decompress_file(hdri.file_path)
                        print(f"  ℹ️  {hdri.name} - HDRI already compressed")
                    except:
                        original = len(hdri.file_path)
                        hdri.file_path = compress_file(hdri.file_path)
                        compressed = len(hdri.file_path)
                        hdri_size += original
                        hdri_comp += compressed
                        print(f"  ✓ {hdri.name} - HDRI: {format_size(original)} → {format_size(compressed)}")
                
                # Compress preview
                if hdri.preview_path:
                    try:
                        decompress_file(hdri.preview_path)
                    except:
                        original = len(hdri.preview_path)
                        hdri.preview_path = compress_file(hdri.preview_path)
                        compressed = len(hdri.preview_path)
                        hdri_size += original
                        hdri_comp += compressed
                        print(f"  ✓ {hdri.name} - Preview: {format_size(original)} → {format_size(compressed)}")
                
                total_original_size += hdri_size
                total_compressed_size += hdri_comp
                if hdri_size > 0:
                    hdri_compressed += 1
                    
            except Exception as e:
                print(f"  ❌ Error compressing {hdri.name}: {str(e)}")
        
        db.session.commit()
        print(f"\n✅ Compressed {hdri_compressed} HDRIs")
        
        # Summary
        print("\n" + "="*60)
        print("COMPRESSION SUMMARY")
        print("="*60)
        print(f"Original Size:    {format_size(total_original_size)}")
        print(f"Compressed Size:  {format_size(total_compressed_size)}")
        print(f"Space Saved:      {format_size(total_original_size - total_compressed_size)}")
        if total_original_size > 0:
            ratio = get_compression_ratio(total_original_size, total_compressed_size)
            print(f"Compression Ratio: {ratio:.1f}% (saved {100-ratio:.1f}%)")
        print("\n✨ Compression complete! Your database is now optimized.")

if __name__ == '__main__':
    compress_existing_files()

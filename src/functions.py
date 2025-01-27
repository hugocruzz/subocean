def export_csv(df, output_path: Path) -> None:
    """Export DataFrame to netCDF format"""
    ds = df.to_xarray()
    ds.to_netcdf(output_path)
    print(f"Exported to {output_path}")
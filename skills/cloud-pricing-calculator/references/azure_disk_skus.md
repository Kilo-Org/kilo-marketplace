# Azure Managed Disk Pricing Tiers

## Premium SSD v1 (Traditional)
| Tier | Size Range | IOPS | Throughput | Typical Use Case |
|------|------------|------|------------|------------------|
| P1 | 4-32 GiB | 120 | 25 MB/s | OS disks, small apps |
| P4 | 32-64 GiB | 120 | 25 MB/s | Small DBs, dev/test |
| P10 | 64-128 GiB | 500 | 100 MB/s | Standard workloads |
| P15 | 128-256 GiB | 1,100 | 125 MB/s | Prod databases |
| P20 | 256-512 GiB | 2,300 | 150 MB/s | High-performance |
| P30 | 512-1024 GiB | 5,000 | 200 MB/s | Mission-critical |

## Premium SSD v2
- Per-GiB pricing + separate IOPS/throughput charges
- More cost-effective for high-capacity, lower-IOPS workloads

## Standard SSD
| Tier | Size Range | IOPS | Throughput |
|------|------------|------|------------|
| E4 | 32-64 GiB | Up to 500 | Up to 60 MB/s |
| E10 | 64-128 GiB | Up to 500 | Up to 60 MB/s |
| E15 | 128-256 GiB | Up to 500 | Up to 60 MB/s |
| E20 | 256-512 GiB | Up to 500 | Up to 60 MB/s |

## Standard HDD
| Tier | Size Range | IOPS | Throughput |
|------|------------|------|------------|
| S4 | 32-64 GiB | Up to 500 | Up to 60 MB/s |
| S10 | 64-128 GiB | Up to 500 | Up to 60 MB/s |
| S15 | 128-256 GiB | Up to 500 | Up to 60 MB/s |
| S20 | 256-512 GiB | Up to 500 | Up to 60 MB/s |

## API Meter Names

For querying Azure Retail Prices API:

| Disk Type | Redundancy | Meter Name Pattern |
|-----------|------------|-------------------|
| Premium SSD | LRS | "P1 Disks", "P4 Disks", "P10 Disks", etc. |
| Premium SSD | ZRS | "P1 ZRS Disks", "P4 ZRS Disks", etc. |
| Standard SSD | LRS | "E4 Disks", "E10 Disks", etc. |
| Standard SSD | ZRS | "E4 ZRS Disks", "E10 ZRS Disks", etc. |
| Standard HDD | LRS | "S4 Disks", "S10 Disks", etc. |
| Standard HDD | ZRS | "S4 ZRS Disks", "S10 ZRS Disks", etc. |

## Real-World Lessons

### Typical Disk Distribution
From a representative 26-disk enterprise inventory:
- 14 Premium SSD (mix of P1, P4, P10, P15) — mostly OS disks
- 4 Standard SSD (all E10) — security and PAM VMs
- 8 Standard HDD (S4, S10, S15) — management and utility VMs

### Cost Optimization Insights
1. **NVA OS disks**: Can be as small as 2 GiB — smallest possible P1 ($0.78/mo)
2. **Security appliance disks**: 127 GiB Standard SSD (E10) — NOT Premium, saving ~$12/disk/mo
3. **Backup storage accounts**: Can grow to tens of TiB — largest cost driver, flag for retention review

### Common Patterns
- OS disks: Usually 127-128 GiB (P10 or E10)
- Data disks: Varies by application
- SQL Express VMs: Often have separate data disks
- Stopped VMs: Still incur disk costs!
